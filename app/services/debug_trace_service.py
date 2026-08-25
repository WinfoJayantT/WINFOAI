"""
Debug Trace Service
===================

This module provides a unified observability and tracing framework for the AI system.
It intercepts and logs LLM intent detection, tool arguments, repository query paths,
and latency timings for display in the WinfoTest frontend.

Key Responsibilities:
  1. Latency Tracking: Captures high-precision timing for vector lookups and LLM generations.
  2. Provenance: Tracks exactly which repository methods were invoked during a request.
  3. Payload Construction: Builds the standard `debug_trace` dictionary appended to all AI responses.
"""

import json
import logging
import uuid
from typing import Any

from app.schemas.debug import DebugTrace

# ── logger initialization ───────────────────────────────────────────────
logger = logging.getLogger(__name__)


# ── class definition ──────────────────────────────────────────────────
class DebugTraceService:
    """
    Central service for constructing and managing AI interaction traces.
    """

    def start_trace(self) -> DebugTrace:
        """
        Initializes a new trace with a unique UUID.
        
        Returns:
            DebugTrace: A fresh, empty trace object.
        """
        return DebugTrace(trace_id=str(uuid.uuid4()))

    def finish_trace(self, trace: DebugTrace, started_at_ms: float) -> DebugTrace:
        """
        Closes a trace, calculates final duration, and logs it to standard output.
        """
        import time

        trace.duration_ms = int((time.perf_counter() - started_at_ms) * 1000)
        logger.info("tool_trace %s", json.dumps(trace.to_dict(), default=str))
        return trace

    def attach_repository_call(self, trace: DebugTrace, method_name: str, records: int = 0) -> None:
        """
        Logs a PostgreSQL or Qdrant query event to the current trace.
        """
        trace.repository_methods.append(method_name)
        trace.records_retrieved += records

    def build_trace(
        self,
        intent: str | None = None,
        tool_name: str | None = None,
        parsed_args: dict[str, Any] | None = None,
        repo_path: str | None = None,
        execution_time_ms: int | None = None,
        warnings: list[str] | None = None,
        errors: list[str] | None = None,
    ) -> DebugTrace:
        """
        Utility method to build a fully hydrated trace in a single step (used primarily by legacy endpoints).
        """
        repo_methods = [repo_path] if repo_path else []
        trace = DebugTrace(
            trace_id=str(uuid.uuid4()),
            detected_intent=intent,
            selected_tool=tool_name,
            parsed_arguments=parsed_args or {},
            repository_methods=repo_methods,
            warnings=warnings or [],
            errors=errors or [],
            duration_ms=execution_time_ms or 0,
        )
        return trace


# ── singleton export ──────────────────────────────────────────────────
debug_trace_service = DebugTraceService()
