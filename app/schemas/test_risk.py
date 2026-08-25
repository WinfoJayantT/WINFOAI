from typing import Any

from pydantic import BaseModel, Field


class RiskAssessmentRequest(BaseModel):
    filter_query: str | None = Field(
        None, description="Optional filter criteria (e.g., 'P2P', 'Supplier', 'AP Invoice', 'module=AP')."
    )
    min_risk_level: str | None = Field(
        "ALL", description="Filter by minimum risk tier (CRITICAL, HIGH, MEDIUM, LOW, ALL)."
    )


class ScriptRiskItem(BaseModel):
    test_script_number: str
    script_name: str
    module: str | None = None
    process_area: str | None = None
    risk_score: int  # 0 to 100
    risk_tier: str   # CRITICAL, HIGH, MEDIUM, LOW
    flakiness_rate: float # 0.0 to 1.0
    total_executions: int
    failed_executions: int
    most_fragile_step: str | None = None
    primary_failure_reason: str | None = None
    stabilization_recommendation: str


class RiskAssessmentResponse(BaseModel):
    status: str
    total_scripts_assessed: int
    high_risk_count: int
    flaky_count: int
    critical_scripts: list[ScriptRiskItem]
    risk_items: list[ScriptRiskItem]
    overall_health_score: int # 0 to 100
    executive_summary: str
    debug_trace: dict[str, Any] | None = None
