from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


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
    error_message: Optional[str] = None
    step_no: Optional[int] = None
    step_action: Optional[str] = None
    locator_repairs: Optional[List[SelfHealingLocatorSuggestion]] = None
    debug_trace: Optional[Dict[str, Any]] = None


class LocatorFixResponse(BaseModel):
    status: str
    script_name: str
    total_broken_locators: int
    locator_repairs: List[SelfHealingLocatorSuggestion]
    healing_summary: str
    debug_trace: Optional[Dict[str, Any]] = None

