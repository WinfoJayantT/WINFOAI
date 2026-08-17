from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RiskAssessmentRequest(BaseModel):
    filter_query: Optional[str] = Field(
        None, description="Optional filter criteria (e.g., 'P2P', 'Supplier', 'AP Invoice', 'module=AP')."
    )
    min_risk_level: Optional[str] = Field(
        "ALL", description="Filter by minimum risk tier (CRITICAL, HIGH, MEDIUM, LOW, ALL)."
    )


class ScriptRiskItem(BaseModel):
    test_script_number: str
    script_name: str
    module: Optional[str] = None
    process_area: Optional[str] = None
    risk_score: int  # 0 to 100
    risk_tier: str   # CRITICAL, HIGH, MEDIUM, LOW
    flakiness_rate: float # 0.0 to 1.0
    total_executions: int
    failed_executions: int
    most_fragile_step: Optional[str] = None
    primary_failure_reason: Optional[str] = None
    stabilization_recommendation: str


class RiskAssessmentResponse(BaseModel):
    status: str
    total_scripts_assessed: int
    high_risk_count: int
    flaky_count: int
    critical_scripts: List[ScriptRiskItem]
    risk_items: List[ScriptRiskItem]
    overall_health_score: int # 0 to 100
    executive_summary: str
    debug_trace: Optional[Dict[str, Any]] = None
