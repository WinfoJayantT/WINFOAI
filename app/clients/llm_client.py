"""
Language Model Client
=====================

This module provides a unified, resilient interface to Large Language Models (LLMs).
It seamlessly handles switching between cloud providers (OpenAI) and local deployments (Ollama)
while enforcing exponential backoff retries, request timeouts, and structured JSON parsing.

Key Responsibilities:
  1. Connection Abstraction: Hides the complexity of configuring the `openai` Python SDK for Ollama endpoints.
  2. Resiliency: Implements a `@with_retry` decorator to gracefully survive rate limits and temporary network drops.
  3. Structured Outputs: Provides native `beta.chat.completions.parse` for OpenAI, and a JSON-parsing
     fallback for local models that don't yet support the beta parsing API.
"""

import logging
import time
from typing import Any, Dict, Optional, Type
from pydantic import BaseModel
from openai import OpenAI
import openai

from app.core.config import settings

# ── logger initialization ───────────────────────────────────────────────
logger = logging.getLogger(__name__)


# ── custom exceptions ───────────────────────────────────────────────────
class LLMTimeoutError(Exception):
    """Raised when the LLM provider fails to respond within the configured timeout window."""
    pass

class LLMRateLimitError(Exception):
    """Raised when the LLM provider actively rate limits the application (HTTP 429)."""
    pass

class LLMServiceError(Exception):
    """Raised for all other generic HTTP/API errors from the LLM provider."""
    pass


# ── resilient networking ────────────────────────────────────────────────
def with_retry(max_retries=3, initial_backoff=1.0):
    """
    Decorator for exponential backoff retries on LLM network calls.
    Specifically traps OpenAI Timeout and RateLimit exceptions.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            backoff = initial_backoff
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except openai.APITimeoutError as e:
                    if attempt == max_retries - 1:
                        raise LLMTimeoutError(f"LLM request timed out after {max_retries} attempts: {e}")
                    logger.warning(f"Timeout on attempt {attempt+1}, retrying in {backoff}s...")
                except openai.RateLimitError as e:
                    if attempt == max_retries - 1:
                        raise LLMRateLimitError(f"LLM rate limited after {max_retries} attempts: {e}")
                    logger.warning(f"Rate limit on attempt {attempt+1}, retrying in {backoff}s...")
                except openai.APIError as e:
                    raise LLMServiceError(f"LLM API error: {e}")
                time.sleep(backoff)
                backoff *= 2
        return wrapper
    return decorator


# ── class definition ──────────────────────────────────────────────────
class LLMClient:
    """
    Singleton client wrapping the OpenAI Python SDK.
    """

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY or "ollama-local"
        self.model = settings.LLM_MODEL
        self.base_url = (
            settings.OLLAMA_BASE_URL if not settings.OPENAI_API_KEY else None
        )
        self._client: Optional[OpenAI] = None

    @property
    def client(self) -> OpenAI:
        """
        Lazily initializes the OpenAI SDK instance, pointing it to Ollama if configured.
        """
        if not self._client:
            timeout = getattr(settings, "LLM_TIMEOUT_SECONDS", 300.0)
            kwargs = {"api_key": self.api_key, "timeout": float(timeout)}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            self._client = OpenAI(**kwargs)
        return self._client

    # ── generation methods ──────────────────────────────────────────────
    @with_retry(max_retries=3)
    def generate_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
        json_mode: bool = False,
        timeout: Optional[float] = None,
        trace_id: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generates a standard raw string completion from the LLM.
        
        Args:
            system_prompt (str): The foundational behavior rules for the model.
            user_prompt (str): The user's query or data payload.
            temperature (float): Determinism level (0.0 = strict, 1.0 = creative).
            json_mode (bool): Forces the model to output valid JSON (if supported).
            
        Returns:
            str: The raw generated text.
        """
        start_time = time.time()
        actual_timeout = timeout or settings.LLM_TIMEOUT_SECONDS
        target_model = model or self.model
        kwargs = {
            "model": target_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "timeout": actual_timeout,
        }

        if max_tokens:
            kwargs["max_tokens"] = max_tokens

        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = self.client.chat.completions.create(**kwargs)
        
        duration = time.time() - start_time
        tokens = response.usage.total_tokens if response.usage else 0
        if trace_id:
            logger.info(f"[TRACE: {trace_id}] generate_completion: {duration:.2f}s, {tokens} tokens, model={self.model}")

        return response.choices[0].message.content

    def generate_stream(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
        timeout: Optional[float] = None,
    ):
        """
        Yields text tokens as they are generated by the LLM, enabling real-time typing effects in the UI.
        """
        actual_timeout = timeout or settings.LLM_TIMEOUT_SECONDS
        kwargs = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "timeout": actual_timeout,
            "stream": True,
        }

        try:
            response = self.client.chat.completions.create(**kwargs)
            for chunk in response:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta and delta.content:
                        yield delta.content
        except Exception as e:
            logger.exception("Error during LLM streaming")
            yield f"\n\n[Error during LLM generation: {str(e)}]"

    @with_retry(max_retries=3)
    def generate_parsed_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        response_format: Type[BaseModel],
        temperature: float = 0.0,
        timeout: Optional[float] = None,
        trace_id: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> BaseModel:
        """
        Forces the LLM to return a strictly typed JSON object matching the provided Pydantic model.
        
        Args:
            response_format (Type[BaseModel]): The Pydantic class defining the target schema.
            
        Returns:
            BaseModel: An instantiated Pydantic object populated with the LLM's response.
        """
        start_time = time.time()
        actual_timeout = timeout or settings.LLM_TIMEOUT_SECONDS
        
        # ── fallback parsing for local models ──
        # Ollama does not natively support the `.beta.chat.completions.parse` method.
        # We manually generate a JSON string and load it into Pydantic.
        if self.base_url:
            raw = self.generate_completion(
                system_prompt, 
                user_prompt, 
                temperature=temperature, 
                timeout=actual_timeout,
                trace_id=trace_id,
                model=model,
                max_tokens=max_tokens,
            )
            import json

            # Clean markdown code blocks (e.g. ```json ... ```)
            clean_raw = raw.strip()
            if clean_raw.startswith("```"):
                clean_raw = clean_raw.split("```")[1]
                if clean_raw.startswith("json"):
                    clean_raw = clean_raw[4:]
            data = json.loads(clean_raw)
            return response_format(**data)

        # ── native openai structured parsing ──
        response = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format=response_format,
            temperature=temperature,
            timeout=actual_timeout,
        )
        
        duration = time.time() - start_time
        tokens = response.usage.total_tokens if response.usage else 0
        if trace_id:
            logger.info(f"[TRACE: {trace_id}] generate_parsed_completion: {duration:.2f}s, {tokens} tokens, model={self.model}")
            
        return response.choices[0].message.parsed


# ── singleton export ──────────────────────────────────────────────────
llm_client = LLMClient()
