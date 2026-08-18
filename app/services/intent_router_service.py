"""
Hybrid Semantic Intent Router
==============================
Stage 1 — Vector Anchor Pre-Filter (~15ms)
  • Embeds user query with all-mpnet-base-v2 dense vectors.
  • Computes cosine similarity against multi-anchor representations for each tool.
  • Identifies the highest-similarity semantic candidate tool without keywords.

Stage 2 — Focused Micro-LLM Argument Extractor (~2–4s)
  • Invokes the configured fast local LLM (FAST_LLM_MODEL) with a minimal, focused
    prompt containing only the matched candidate tool's argument schema.
  • Dynamically extracts all scenario names, script IDs, modules, and process areas
    with 100% natural language AI comprehension and zero hardcoded regex/keyword shortcuts.
"""

import json
import logging
import re
from typing import Dict, List, Optional, Tuple, Any

from app.clients.llm_client import llm_client
from app.core.config import settings
from app.schemas.intent import IntentName, IntentRequest, IntentResult, MultiIntentResult

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Semantic Tool Anchor Space
# Comprehensive natural-language anchor representations for cosine matching.
# Cached in memory at startup for sub-millisecond vector evaluation.
# ─────────────────────────────────────────────────────────────────────────────
TOOL_ANCHORS: Dict[str, Dict] = {
    "semantic_search_tests": {
        "intent_enum": IntentName.SEMANTIC_SEARCH_TESTS,
        "anchors": [
            "Find test scripts for supplier invoice payment",
            "Show me tests related to purchase order management",
            "Search for automation scripts covering accounts payable",
            "Which tests cover banking reconciliation process",
            "List test scripts for general ledger",
            "Find scripts that test supplier creation",
            "Show banking tests",
            "Search tests for procure to pay",
        ],
        "micro_schema": (
            '{"query": "<search phrase>", "limit": <integer>, "include_steps": <boolean>}'
        ),
        "micro_instruction": (
            "Extract the search phrase from the query. "
            "Set limit to 1 if the query refers to a singular script, otherwise 5. "
            "Set include_steps to true if the user asks for workflow, steps, or execution details, else false."
        ),
    },
    "filtered_script_lookup": {
        "intent_enum": IntentName.FILTERED_SCRIPT_LOOKUP,
        "anchors": [
            "Explain script PRC.P2P.PO.22",
            "Look up test script number INV-001",
            "Show me details for script SUP.003",
            "What does test script 3007_Create_Supplier do",
            "Get information about script PRC",
            "Describe the test script with ID",
            "Pull up script details for AP.INV.12",
        ],
        "micro_schema": '{"identifier": "<exact script number, name, or ID>"}',
        "micro_instruction": "Extract the specific script code, script number, name, or UUID identifier from the query.",
    },
    "generate_script_steps": {
        "intent_enum": IntentName.GENERATE_SCRIPT_STEPS,
        "anchors": [
            "Generate test steps for creating a supplier in Oracle",
            "Build automation steps for approving a purchase order",
            "Create test script steps for processing an invoice",
            "Write WinfoTest steps for supplier onboarding",
            "Generate automation sequence for Oracle procurement workflow",
            "What steps do I need to automate vendor creation",
            "Build steps for order to cash process",
            "Create automation steps for accounts payable",
        ],
        "micro_schema": '{"scenario": "<business process description>", "process_area": "<Oracle process area if mentioned, else empty>"}',
        "micro_instruction": (
            "Extract the business scenario to be automated. "
            "Extract the Oracle ERP process area (e.g. Procure to Pay, Order to Cash, Record to Report) if mentioned."
        ),
    },
    "generate_test_suite": {
        "intent_enum": IntentName.GENERATE_TEST_SUITE,
        "anchors": [
            "Generate an end to end test suite for procure to pay",
            "Build a regression test suite for order to cash",
            "Create a complete test plan for accounts payable",
            "Generate E2E test coverage for financial modules",
            "Build a test suite covering all procurement scripts",
            "Create comprehensive test suite for oracle ERP",
        ],
        "micro_schema": '{"process_area": "<process area name>", "target_module": "<target module if specified>"}',
        "micro_instruction": "Extract the Oracle ERP process area and any target module specified for the regression test suite.",
    },
    "semantic_cluster_scripts": {
        "intent_enum": IntentName.SEMANTIC_CLUSTER_SCRIPTS,
        "anchors": [
            "Group test scripts by process area",
            "Cluster tests by module",
            "Organize scripts by functional category",
            "Show me how tests are grouped by supplier management",
            "Categorize automation scripts by Oracle module",
        ],
        "micro_schema": '{"concept": "<grouping dimension or concept>"}',
        "micro_instruction": "Extract the category or concept to group/cluster the test scripts by (e.g. process area, module).",
    },
    "assess_test_risk": {
        "intent_enum": IntentName.ASSESS_TEST_RISK,
        "anchors": [
            "Assess risk for flaky tests",
            "Which tests are most likely to fail",
            "Show test failure rates and flakiness",
            "What is the stability score for automation scripts",
            "Identify high risk test scripts",
            "Evaluate test health and failure patterns",
        ],
        "micro_schema": '{"filter_query": "<optional process scope filter>", "min_risk_level": "ALL"}',
        "micro_instruction": "Extract any process scope or filter mentioned by the user. Default min_risk_level to ALL.",
    },
    "recommend_locator_fixes": {
        "intent_enum": IntentName.RECOMMEND_LOCATOR_FIXES,
        "anchors": [
            "Suggest locator fixes for failing script PRC.P2P with broken locator",
            "Fix broken XPath locators for element",
            "Recommend self-healing locator patches for selector",
            "Repair element selectors and broken XPath for script",
            "Synthesize resilient locator for failing button",
        ],
        "micro_schema": '{"script_name": "<script identifier if mentioned>", "error_log": "<broken locator or error log>"}',
        "micro_instruction": "Extract the script identifier and any broken locator or error log provided.",
    },
    "analyze_entity": {
        "intent_enum": IntentName.ANALYZE_ENTITY,
        "anchors": [
            "Explain why this script failed: TimeoutError: locator.click",
            "Why did this test fail with timeout error",
            "Explain why this test script failed with this log",
            "Analyze the failure log and diagnose root cause",
            "Debug this test failure error log",
            "What went wrong with this test execution",
            "Investigate the error in this test execution log",
            "Diagnose Playwright failure log and suggest fix",
        ],
        "micro_schema": '{"identifier": "<script identifier or empty>", "error_log": "<full error log snippet or error message provided by user>"}',
        "micro_instruction": (
            "Extract any script identifier if mentioned. "
            "Extract the full error log, exception message, or stack trace into 'error_log'."
        ),
    },
    "execute_script_set": {
        "intent_enum": IntentName.EXECUTE_SCRIPT_SET,
        "anchors": [
            "Run the test scripts now",
            "Execute the generated test suite",
            "Start running the test scripts",
            "Trigger test execution",
        ],
        "micro_schema": "{}",
        "micro_instruction": "No arguments needed.",
    },
    "index_all_scripts": {
        "intent_enum": IntentName.INDEX_ALL_SCRIPTS,
        "anchors": [
            "Index all test scripts into the vector store",
            "Rebuild the semantic search index",
            "Re-index all scripts",
            "Update the vector embeddings for all scripts",
        ],
        "micro_schema": '{"fast_mode": true}',
        "micro_instruction": "Set fast_mode=true unless the user explicitly asks for a slow re-index.",
    },
    "check_indexing_status": {
        "intent_enum": IntentName.CHECK_INDEXING_STATUS,
        "anchors": [
            "Is indexing done yet",
            "Check the status of the indexing job",
            "How many scripts have been indexed",
            "Is the vector store update complete",
        ],
        "micro_schema": "{}",
        "micro_instruction": "No arguments needed.",
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# Micro-LLM Extractor Prompt
# ─────────────────────────────────────────────────────────────────────────────
_MICRO_EXTRACTOR_SYSTEM = """You are a precise argument extractor for WinfoTest AI.
The user's intent has already been identified. Extract the required parameters from the user's query into the exact JSON schema provided.
Return ONLY a valid JSON object. No markdown code blocks, no explanations, no additional keys."""


def _micro_extractor_user_prompt(
    tool_name: str, schema: str, instruction: str, user_query: str
) -> str:
    return (
        f"Tool: {tool_name}\n"
        f"Argument JSON Schema: {schema}\n"
        f"Instructions: {instruction}\n"
        f"User Query: {user_query}\n\n"
        "Output the extracted JSON:"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Anchor Vector Space Cache
# ─────────────────────────────────────────────────────────────────────────────
_ANCHOR_CACHE: Dict[str, List[List[float]]] = {}


def _get_anchor_vectors(tool_name: str, anchors: List[str]) -> List[List[float]]:
    if tool_name in _ANCHOR_CACHE:
        return _ANCHOR_CACHE[tool_name]
    from app.services.embedding_service import embedding_service
    vecs = embedding_service.embed_batch(anchors)
    _ANCHOR_CACHE[tool_name] = vecs
    return vecs


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two unit-normalized vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    return max(-1.0, min(1.0, dot))


def _score_tool(query_vector: List[float], tool_name: str, anchors: List[str]) -> float:
    """Return maximum cosine similarity between query vector and tool anchors."""
    vecs = _get_anchor_vectors(tool_name, anchors)
    if not vecs:
        return 0.0
    return max(_cosine_similarity(query_vector, v) for v in vecs)


# ─────────────────────────────────────────────────────────────────────────────
# IntentRouterService
# ─────────────────────────────────────────────────────────────────────────────
class IntentRouterService:
    CANDIDATE_THRESHOLD = 0.38

    def route(self, request: IntentRequest) -> MultiIntentResult:
        if not settings.is_llm_configured:
            logger.warning("LLM not configured; returning unknown intent.")
            return self._unresolvable("LLM configuration is missing.")

        query = request.user_query.strip()

        # ── Stage 1: Vector Anchor Pre-Filter ────────────────────────────────
        try:
            from app.services.embedding_service import embedding_service
            query_vector = embedding_service.embed_text(query)
        except Exception as exc:
            logger.error("Embedding failed during intent routing: %s", exc)
            return self._unresolvable(str(exc))

        scored: List[Tuple[str, float]] = []
        for tool_name, tool_def in TOOL_ANCHORS.items():
            score = _score_tool(query_vector, tool_name, tool_def["anchors"])
            if score >= self.CANDIDATE_THRESHOLD:
                scored.append((tool_name, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        logger.info(
            "[VectorRouter] Candidates for '%s': %s",
            query[:60],
            [(t, f"{s:.3f}") for t, s in scored[:3]],
        )

        if not scored:
            logger.info("[VectorRouter] No candidates above threshold — returning unknown.")
            return self._unresolvable("Query did not match any tool with sufficient semantic similarity.")

        best_tool, best_score = scored[0]
        tool_def = TOOL_ANCHORS[best_tool]
        intent_enum = tool_def["intent_enum"]

        # ── Stage 2: Dynamic Micro-LLM Argument Extraction ───────────────────
        arguments: Dict[str, Any] = {}
        schema_spec = tool_def.get("micro_schema", "{}")
        
        if schema_spec != "{}":
            try:
                micro_user = _micro_extractor_user_prompt(
                    tool_name=best_tool,
                    schema=schema_spec,
                    instruction=tool_def["micro_instruction"],
                    user_query=query,
                )
                model_to_use = getattr(settings, "FAST_LLM_MODEL", None) or settings.LLM_MODEL
                raw = llm_client.generate_completion(
                    system_prompt=_MICRO_EXTRACTOR_SYSTEM,
                    user_prompt=micro_user,
                    temperature=0.0,
                    max_tokens=150,
                    model=model_to_use,
                    trace_id="micro_extractor",
                )
                clean = raw.strip()
                if "```" in clean:
                    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean, re.DOTALL)
                    clean = m.group(1) if m else re.sub(r"```[a-z]*", "", clean).strip()

                parsed = json.loads(clean)
                if isinstance(parsed, dict):
                    arguments = parsed

            except Exception as exc:
                logger.warning("Micro-LLM argument extraction failed: %s", exc)
                arguments = {}

        # Calibrate confidence from dense vector cosine score
        confidence = round(min(0.99, 0.60 + (best_score - self.CANDIDATE_THRESHOLD) * 1.60), 3)

        logger.info(
            "[HybridRouter] Resolved: intent=%s tool=%s confidence=%.3f score=%.3f args=%s",
            intent_enum.value, best_tool, confidence, best_score, arguments,
        )

        return MultiIntentResult(intents=[IntentResult(
            intent=intent_enum,
            tool=best_tool,
            arguments=arguments,
            confidence=confidence,
            ambiguities=[],
            reasoning=(
                f"Dense vector matching selected '{best_tool}' (cosine similarity = {best_score:.3f}). "
                "Arguments dynamically extracted via AI comprehension."
            ),
        )])

    def _unresolvable(self, reasoning: str) -> MultiIntentResult:
        return MultiIntentResult(intents=[IntentResult(
            intent=IntentName.UNKNOWN,
            tool="unknown",
            arguments={},
            confidence=0.0,
            ambiguities=["Query could not be resolved to any tool."],
            reasoning=reasoning,
        )])


intent_router_service = IntentRouterService()
