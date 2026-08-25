from dataclasses import dataclass, field
from typing import Any


@dataclass
class DebugTrace:
    trace_id: str
    detected_intent: str | None = None
    selected_tool: str | None = None
    parsed_arguments: dict[str, Any] = field(default_factory=dict)
    repository_methods: list[str] = field(default_factory=list)
    records_retrieved: int = 0
    vector_search_used: bool = False
    llm_used: bool = False
    ambiguities: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    duration_ms: int | None = None

    def to_dict(self) -> dict[str, Any]:
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
