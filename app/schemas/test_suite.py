from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TestSuiteRequest(BaseModel):
    process_area: Optional[str] = Field(
        None, description="The business process area (e.g., 'Procure to Pay', 'Order to Cash', 'Record to Report')."
    )
    process_flow: Optional[str] = Field(
        None, description="The specific end-to-end process flow or business objective."
    )
    target_module: Optional[str] = Field(
        None, description="Optional target ERP module (e.g. 'AP', 'PO', 'GL', 'AR')."
    )


class TestSuiteStepItem(BaseModel):
    step_sequence: int
    test_script_number: str
    script_name: str
    process_name: Optional[str] = None
    module: Optional[str] = None
    business_role: Optional[str] = None
    step_objective: str
    estimated_duration_mins: float = 2.0


class CoverageGapItem(BaseModel):
    process_stage: str
    missing_capability: str
    risk_level: str  # HIGH, MEDIUM, LOW
    recommendation: str


class TestSuiteResponse(BaseModel):
    status: str
    suite_name: str
    process_area: str
    suite_description: str
    total_scripts: int
    estimated_total_duration_mins: float
    execution_steps: List[TestSuiteStepItem]
    coverage_gaps: List[CoverageGapItem]
    reasoning: str
    debug_trace: Optional[Dict[str, Any]] = None
