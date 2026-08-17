from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ClusterRequest(BaseModel):
    concept: str = Field(
        ...,
        description="The concept or criteria to cluster scripts by (e.g., 'risk level', 'process area', 'EU tax vs US tax').",
    )
    filter_query: Optional[str] = Field(
        None, description="Optional pre-filter (e.g., 'supplier' or 'module=AP')."
    )


class RawClusterOutput(BaseModel):
    """Strict JSON structure enforced on the LLM via OpenAI Structured Outputs."""

    clusters: Dict[str, List[str]] = Field(
        ...,
        description="Mapping of dynamic cluster category names to lists of exact test_script_numbers.",
    )
    reasoning: str = Field(
        ..., description="Short explanation of how the clusters were derived."
    )


class ClusterResponse(BaseModel):
    status: str
    concept: str
    clusters: Dict[str, List[Dict[str, Any]]]
    reasoning: str
    total_scripts_matched: int
