# STREAMING_CHUNK:Defining intent schema and resilient pydantic validation...
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, model_validator


class IntentName(str, Enum):
    SEMANTIC_CLUSTER_SCRIPTS = "semantic_cluster_scripts"
    SEMANTIC_SEARCH_TESTS = "semantic_search_tests"
    FILTERED_SCRIPT_LOOKUP = "filtered_script_lookup"
    ANALYZE_ENTITY = "analyze_entity"
    EXECUTE_SCRIPT_SET = "execute_script_set"
    GENERATE_TEST_SUITE = "generate_test_suite"
    RECOMMEND_LOCATOR_FIXES = "recommend_locator_fixes"
    ASSESS_TEST_RISK = "assess_test_risk"
    INDEX_ALL_SCRIPTS = "index_all_scripts"
    CHECK_INDEXING_STATUS = "check_indexing_status"
    GENERATE_SCRIPT_STEPS = "generate_script_steps"
    UNKNOWN = "unknown"


class IntentRequest(BaseModel):
    user_query: str = Field(
        ..., description="The natural language query from the user."
    )
    conversation_context: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional conversation state context."
    )


class IntentResult(BaseModel):
    intent: IntentName = Field(..., description="The classified intent enum.")
    tool: Optional[str] = Field(
        default=None, description="The name of the backend tool to execute."
    )
    arguments: Dict[str, Any] = Field(
        default_factory=dict, description="Extracted arguments for the tool."
    )
    confidence: float = Field(
        default=1.0, description="Confidence score from 0.0 to 1.0."
    )
    ambiguities: list[str] = Field(
        default_factory=list, description="Array of vague phrases or ambiguous entities."
    )
    reasoning: str = Field(
        default="", description="Explanation for why this intent and tool were chosen."
    )

    @model_validator(mode="after")
    def infer_tool_and_defaults(self) -> "IntentResult":
        if not self.tool or self.tool == "unknown":
            if self.intent != IntentName.UNKNOWN:
                self.tool = self.intent.value
            else:
                self.tool = "unknown"
        return self

class MultiIntentResult(BaseModel):
    intents: list[IntentResult] = Field(
        default_factory=list, description="List of recognized intents in the query."
    )

    @property
    def primary_intent(self) -> IntentResult:
        if self.intents:
            return self.intents[0]
        return IntentResult(
            intent=IntentName.UNKNOWN,
            tool="unknown",
            arguments={},
            confidence=0.0,
            ambiguities=["No intent found."],
            reasoning="Empty intent list",
        )
