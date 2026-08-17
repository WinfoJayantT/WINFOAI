from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class DebugTrace:
    trace_id: str
    detected_intent: Optional[str] = None
    selected_tool: Optional[str] = None
    parsed_arguments: Dict[str, Any] = field(default_factory=dict)
    repository_methods: List[str] = field(default_factory=list)
    records_retrieved: int = 0
    vector_search_used: bool = False
    llm_used: bool = False
    ambiguities: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    duration_ms: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "detected_intent": self.detected_intent,
            "selected_tool": self.selected_tool,
            "parsed_arguments": self.parsed_arguments,
            "repository_methods": self.repository_methods,
            "records_retrieved": self.records_retrieved,
            "vector_search_used": self.vector_search_used,
            "llm_used": self.llm_used,
            "ambiguities": self.ambiguities,
            "warnings": self.warnings,
            "errors": self.errors,
            "duration_ms": self.duration_ms,
        }
