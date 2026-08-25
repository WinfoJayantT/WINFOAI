from typing import Any

from pydantic import BaseModel


class FailureAnalysisRequest(BaseModel):
    identifier: str


class SelfHealingLocatorSuggestion(BaseModel):
    step_no: int
    step_action: str
    broken_locator: str
    suggested_locator: str
    selector_type: str = "xpath"  # "xpath" or "css"
    confidence: float
    fix_rationale: str
    resilience_score: int  # 0 to 100


class FailureAnalysisResponse(BaseModel):
    status: str
    explanation: str
    suggested_fix: str
    confidence: float
    error_message: str | None = None
    step_no: int | None = None
    step_action: str | None = None
    locator_repairs: list[SelfHealingLocatorSuggestion] | None = None
    debug_trace: dict[str, Any] | None = None


class LocatorFixResponse(BaseModel):
    status: str
    script_name: str
    total_broken_locators: int
    locator_repairs: list[SelfHealingLocatorSuggestion]
    healing_summary: str
    debug_trace: dict[str, Any] | None = None

