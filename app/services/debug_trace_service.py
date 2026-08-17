import json
import logging
import uuid
from typing import Any, Dict, List, Optional

from app.schemas.debug import DebugTrace

logger = logging.getLogger(__name__)


class DebugTraceService:
    def start_trace(self) -> DebugTrace:
        return DebugTrace(trace_id=str(uuid.uuid4()))

    def finish_trace(self, trace: DebugTrace, started_at_ms: float) -> DebugTrace:
        import time

        trace.duration_ms = int((time.perf_counter() - started_at_ms) * 1000)
        logger.info("tool_trace %s", json.dumps(trace.to_dict(), default=str))
        return trace

    def attach_repository_call(self, trace: DebugTrace, method_name: str, records: int = 0) -> None:
        trace.repository_methods.append(method_name)
        trace.records_retrieved += records

    def build_trace(
        self,
        intent: Optional[str] = None,
        tool_name: Optional[str] = None,
        parsed_args: Optional[Dict[str, Any]] = None,
        repo_path: Optional[str] = None,
        execution_time_ms: Optional[int] = None,
        warnings: Optional[List[str]] = None,
        errors: Optional[List[str]] = None,
    ) -> DebugTrace:
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


debug_trace_service = DebugTraceService()
