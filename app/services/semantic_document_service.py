"""
Semantic Document Generation Service
====================================

This module bridges the gap between raw database automation scripts and natural language 
by generating rich, human-readable "Semantic Documents".

These documents are crucial for two reasons:
  1. Vector Search Indexing: They provide a dense narrative block of text that `all-mpnet-base-v2`
     can accurately embed for highly semantic search results.
  2. UI Presentation: They are streamed to the WinfoTest UI so non-technical users
     (like business analysts) can immediately understand what a complex technical script does.

Key Capabilities:
  - MBP Mapping: Cross-references a script's module against `oracle_mbp_mappings.json` to 
    tag it with standard Oracle Modern Best Practice hierarchies (e.g. Procure to Pay).
  - Dual Generation modes: Uses the LLM for deep contextual generation by default, falling
    back to a deterministic string formatter (`generate_local_semantic_document`) if the LLM is down.
"""

import json
import logging
import os
from typing import Any

from app.clients.llm_client import llm_client
from app.core.config import settings

# ── logger initialization ───────────────────────────────────────────────
logger = logging.getLogger(__name__)

NOT_SPECIFIED = "Not specified in source data"

# ── prompt engineering ──────────────────────────────────────────────────
SEMANTIC_DOCUMENT_SYSTEM_PROMPT = """You are an Enterprise ERP QA & Semantic Test Analysis Expert specializing in Oracle Fusion Cloud Applications.
Your task is to analyze a raw test script (including qualified name, metadata, and ordered UI/API steps) and produce an exhaustive, structured 'Semantic Document'.

You MUST format your output as a clean, standardized Markdown text block with exactly 5 sections:

1. Process Area & ERP Hierarchy
2. Business Objective & Functional Scope
3. End-to-End Transactional Workflow & Navigation
4. Input Parameters & Master Data Requirements
5. Expected Business Validations & Audit Checkpoints

CRITICAL: Do NOT include script IDs, UUIDs, raw locators, or technical UI selectors.
Only state a Process Area, Process, Module, or Role if provided in the context; otherwise write "Not specified in source data".
"""


# ── class definition ──────────────────────────────────────────────────
class SemanticDocumentService:
    """
    Transforms raw database step records into narrative Markdown documents for vector indexing
    and user-facing explanations.
    """

    def __init__(self, client=None):
        self.client = client or llm_client
        self._mbp_mappings = self._load_mbp_mappings()
        
    def _load_mbp_mappings(self) -> list[dict[str, Any]]:
        """Loads static mapping of Winfo modules to standard Oracle Modern Best Practices."""
        try:
            config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'oracle_mbp_mappings.json')
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load MBP mappings from config/oracle_mbp_mappings.json: {e}")
            return []

    def _is_valid_semantic_document(self, text: str | None) -> bool:
        """Heuristically checks if the LLM followed the strict 5-section markdown structure."""
        if not text or len(text.strip()) < 100:
            return False
        clean = text.lower()
        required_markers = [
            "process",
            "objective",
            "workflow",
            "parameter",
            "validation",
        ]
        matches = sum(1 for m in required_markers if m in clean)
        return matches >= 3

    # ── llm generation ──────────────────────────────────────────────────
    def generate_semantic_document(
        self, script_data: dict[str, Any], steps: list[dict[str, Any]]
    ) -> str:
        """
        Invokes the configured LLM to generate a deep-context narrative document.
        
        Args:
            script_data (Dict): Raw row from test_scripts table.
            steps (List): Raw rows from master_steps table.
            
        Returns:
            str: 5-section Markdown text.
            
        Raises:
            ValueError: If the LLM goes off-rails and ignores the schema constraints.
        """
        formatted_steps = []
        for step in steps[:30]:  # Limit to 30 steps to prevent prompt explosion
            seq = step.get("step_sequence", step.get("step_no", "?"))
            action = step.get("step_action", step.get("action", ""))
            desc = step.get("step_description", step.get("step_name", ""))
            formatted_steps.append(f"Step {seq}: {action} - {desc}")

        steps_text = (
            "\n".join(formatted_steps)
            if formatted_steps
            else "No step details provided."
        )

        mbp_context = ""
        process_name = script_data.get('process')
        if process_name and self._mbp_mappings:
            matched = [m for m in self._mbp_mappings if m["l1_process"].lower() == process_name.lower() or m["l2_process"].lower() == process_name.lower()]
            if matched:
                mbp_context = "\nOracle Modern Best Practice (MBP) Context:\n"
                for m in matched:
                    mbp_context += f"- L1 Process: {m['l1_process']} | L2 Process: {m['l2_process']}\n"

        user_prompt = f"""Qualified Name: {script_data.get('qualified_name', 'N/A')}
Title: {script_data.get('script_name', 'N/A')}
Module: {script_data.get('module') or NOT_SPECIFIED}
Process: {script_data.get('process') or NOT_SPECIFIED}
Description: {script_data.get('description', '')}
{mbp_context}
Ordered Workflow Steps:
{steps_text}
"""
        try:
            model_to_use = getattr(settings, "FAST_LLM_MODEL", None) or settings.LLM_MODEL
            semantic_doc = self.client.generate_completion(
                system_prompt=SEMANTIC_DOCUMENT_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.0,
                max_tokens=750,
                model=model_to_use,
                trace_id="semantic_document_gen",
            )
            if self._is_valid_semantic_document(semantic_doc):
                return semantic_doc.strip()
            else:
                raise ValueError("LLM generated document did not meet quality/schema criteria.")
        except Exception as e:
            logger.error(f"LLM API call encountered an error: {e}")
            raise

    # ── local generation fallback ───────────────────────────────────────
    def generate_local_semantic_document(
        self, script_data: dict[str, Any], steps: list[dict[str, Any]]
    ) -> str:
        """
        Deterministically formats the 5-section semantic document natively in Python 
        without invoking the LLM. Used as an ultra-fast fallback or for batch processing.
        """
        formatted_steps = []
        for step in steps[:30]:
            seq = step.get("step_sequence", step.get("step_no", "?"))
            action = step.get("step_action", step.get("action", ""))
            desc = step.get("step_description", step.get("step_name", ""))
            formatted_steps.append(f"Step {seq}: {action} - {desc}")

        steps_text = (
            "\n".join(formatted_steps)
            if formatted_steps
            else "No step details provided in source database."
        )

        title = script_data.get('script_name', 'Unknown')
        q_name = script_data.get('qualified_name', 'N/A')
        module = script_data.get('module') or NOT_SPECIFIED
        process = script_data.get('process') or NOT_SPECIFIED
        desc = script_data.get('description') or 'Standard ERP end-to-end execution workflow.'

        mbp_info = "Not specified in source data"
        if process and self._mbp_mappings:
            matched = [m for m in self._mbp_mappings if m["l1_process"].lower() == process.lower() or m["l2_process"].lower() == process.lower()]
            if matched:
                mbp_info = ", ".join([f"{m['l1_process']} -> {m['l2_process']}" for m in matched])

        params = [str(s.get('input_parameter')) for s in steps if s.get('input_parameter')]
        params_str = ", ".join(params) if params else "None specified in source steps."

        doc = f"""# 1. Process Area & ERP Hierarchy
- Process Area: {process}
- Module: {module}
- ERP Modern Best Practice Alignment: {mbp_info}

# 2. Business Objective & Functional Scope
- Script Name: {title} ({q_name})
- Functional Objective: {desc}

# 3. End-to-End Transactional Workflow & Navigation
{steps_text}

# 4. Input Parameters & Master Data Requirements
- Parameters: {params_str}

# 5. Expected Business Validations & Audit Checkpoints
- Automated validation of workflow execution and status checkpoints.
"""
        return doc.strip()

    # ── caching entrypoint ──────────────────────────────────────────────
    def get_or_create_semantic_document(
        self, script_data: dict[str, Any], steps: list[dict[str, Any]], only_allow_cache: bool = False
    ) -> str:
        """
        Retrieves a pre-computed document from PostgreSQL if it exists, otherwise generates it
        and saves it back to the database.
        
        Args:
            script_data (Dict): The test_scripts row.
            steps (List): The master_steps rows.
            only_allow_cache (bool): If True, falls back to local string formatting instead of LLM generation
                                     if not in cache (used for fast bulk search responses).
        """
        script_id = script_data.get("id")
        if not script_id:
            raise ValueError("Script ID is required to fetch or create a semantic document.")
            
        from app.repositories.index_repository import index_repository
        
        # 1. Check DB Cache
        cached = index_repository.get_semantic_document(script_id)
        if cached and cached.get("semantic_document"):
            return cached.get("semantic_document")

        # 2. Try LLM Generation
        if settings.is_llm_configured and not only_allow_cache:
            try:
                doc = self.generate_semantic_document(script_data, steps)
                index_repository.record_semantic_document(script_id, doc, "llm")
                return doc
            except Exception as e:
                logger.warning(f"Dynamic LLM semantic doc generation fallback: {e}")
                doc = self.generate_local_semantic_document(script_data, steps)
                index_repository.record_semantic_document(script_id, doc, "pg_schema")
                return doc

        # 3. Fallback to ultra-fast native generation
        return self.generate_local_semantic_document(script_data, steps)

# ── singleton export ──────────────────────────────────────────────────
semantic_document_service = SemanticDocumentService()
