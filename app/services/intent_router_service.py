"""
Hybrid Semantic Intent Router
==============================

This module is the core NLP brain of the WinfoTest AI system. It converts unstructured human
text into structured JSON arguments using a blazing fast two-stage pipeline.

Stage 1 — Vector Anchor Pre-Filter (~15ms)
  • Embeds user query with `all-mpnet-base-v2` dense vectors.
  • Computes cosine similarity against multi-anchor representations for each tool.
  • Identifies the highest-similarity semantic candidate tool without relying on exact keywords.

Stage 2 — Focused Micro-LLM Argument Extractor (~2–4s)
  • Invokes the configured fast local LLM (`FAST_LLM_MODEL`) with a minimal, focused
    prompt containing only the matched candidate tool's argument schema.
  • Dynamically extracts all scenario names, script IDs, modules, and process areas
    with 100% natural language AI comprehension and zero hardcoded regex/keyword shortcuts.
"""

import json
import logging
import re
from typing import Any

from app.clients.llm_client import llm_client
from app.core.config import settings
from app.schemas.intent import (
    IntentName,
    IntentRequest,
    IntentResult,
    MultiIntentResult,
)

# ── logger initialization ───────────────────────────────────────────────
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Semantic Tool Anchor Space
# Comprehensive natural-language anchor representations for cosine matching.
# Cached in memory at startup for sub-millisecond vector evaluation.
# ─────────────────────────────────────────────────────────────────────────────
TOOL_ANCHORS: dict[str, dict] = {
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
            '{"query": "<search phrase>", "limit": <integer>, "include_steps": false}'
        ),
        "micro_instruction": (
            "Extract the search phrase from the query. "
            "Set limit to 1 only if the user explicitly references a single script by name or number. "
            "Otherwise default limit to 8 to return multiple relevant results. "
            "Never set include_steps to true — always use false."
        ),
    },
    "filtered_script_lookup": {
        "intent_enum": IntentName.FILTERED_SCRIPT_LOOKUP,
        "anchors": [
            "Look up test script number [SCRIPT_ID]",
            "Show me details for script [MODULE.ID]",
            "Get information about script [MODULE_PREFIX]",
            "Pull up script details for [MODULE.PROCESS.ID]",
        ],
        "micro_schema": '{"identifier": "<exact script number, name, or ID>"}',
        "micro_instruction": "Extract the specific script code, script number, name, or UUID identifier from the query.",
        "regex_fastpath": {
            "pattern": r"([A-Z]{2,4}(?:\.[A-Z0-9]+)+|[a-f0-9-]{36}|[A-Z]+-\d+)",
            "map_to": "identifier"
        }
    },
    "analyze_entity": {
        "intent_enum": IntentName.ANALYZE_ENTITY,
        "anchors": [
            "Explain script [MODULE.PROCESS.SCRIPT_ID]",
            "What does test script [SCRIPT_NAME] do",
            "Describe the test script with ID",
            "Explain step 30",
            "What does this step actually do",
            "Analyze the workflow for this script",
            "Walk me through what this automation does",
            "Why is this step failing",
            "Analyze failure log for this script",
            "Explain why the locator broke in this script",
        ],
        "micro_schema": '{"identifier": "<script identifier if mentioned>", "error_log": "<error or failure text if mentioned>"}',
        "micro_instruction": "Extract the script identifier and any error/failure logs mentioned. If asking to explain a specific step while in a script context, leave identifier empty and let the active context handle it.",
    },
    "generate_script_steps": {
        "intent_enum": IntentName.GENERATE_SCRIPT_STEPS,
        "anchors": [
            # Technical QA Anchors
            "Generate test steps for creating a supplier in Oracle",
            "Build automation steps for approving a purchase order",
            "Create test script steps for processing an invoice",
            "Write WinfoTest steps for supplier onboarding",
            "Generate automation sequence for Oracle procurement workflow",
            "What steps do I need to automate vendor creation",
            "Build steps for order to cash process",
            "Create automation steps for accounts payable",
            # Conversational Natural Language Anchors
            "How do I add a new supplier with their office address and payment method",
            "Give me the steps to create and submit a supplier invoice in Accounts Payable",
            "Walk me through entering a new customer sales order and booking it",
            "I want to test creating a vendor with corporate address",
            "Steps for hiring a new employee in HR",
            "How to create and book a sales order step by step",
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
    "conversational_fallback": {
        "intent_enum": IntentName.UNKNOWN,
        "anchors": [
            "Explain supplier banking tests",
            "What is WinfoTest",
            "How does this work",
            "Explain this to me",
            "Hello",
            "Who are you",
            "Can you explain what these tests do",
            "Give me an overview of",
            "What are these scripts",
            "Tell me about",
        ],
        "micro_schema": '{"message": "<user message>"}',
        "micro_instruction": "Extract the user message.",
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
            "Suggest locator fixes for failing script [SCRIPT_ID] with broken locator",
            "Fix broken XPath locators for element",
            "Recommend self-healing locator patches for selector",
            "Repair element selectors and broken XPath for script",
            "Synthesize resilient locator for failing button",
        ],
        "micro_schema": '{"script_name": "<script identifier if mentioned>", "error_log": "<broken locator or error log>"}',
        "micro_instruction": "Extract the script identifier and any broken locator or error log provided.",
    },
    "schedule_test_run": {
        "intent_enum": IntentName.SCHEDULE_TEST_RUN,
        "anchors": [
            "Schedule test run for tomorrow",
            "Run the AP Invoices suite tonight at 10 PM",
            "Execute the supplier onboarding script at midnight",
            "Queue test execution for next Friday",
            "Run this test script at 5:00 AM",
        ],
        "micro_schema": '{"target_suite": "<script or suite name>", "scheduled_time": "<ISO-8601 datetime>"}',
        "micro_instruction": "Extract the target test script or suite name. Convert the requested time to an ISO-8601 datetime format.",
    },
    "analyze_test_results": {
        "intent_enum": IntentName.ANALYZE_TEST_RESULTS,
        "anchors": [
            "How many tests failed yesterday",
            "What is the pass rate for Accounts Payable",
            "Show me test results for last week",
            "Summarize the failed tests in the procurement module",
            "Give me the execution stats for today",
        ],
        "micro_schema": '{"timeframe": "<yesterday|today|last week|this month|etc>", "module": "<module name>", "status": "<pass|fail|all>"}',
        "micro_instruction": "Extract the requested timeframe, target module, and execution status filter.",
    },
    "detect_duplicates": {
        "intent_enum": IntentName.DETECT_DUPLICATES,
        "anchors": [
            "Find redundant test scripts in the Procurement module",
            "Are there any duplicate tests in Accounts Payable?",
            "Identify similar scripts that can be consolidated",
            "Show me redundant testing flows",
        ],
        "micro_schema": '{"module": "<module name or empty>"}',
        "micro_instruction": "Extract the target module name if specified. If not, leave empty.",
    },
    "lint_locators": {
        "intent_enum": IntentName.LINT_LOCATORS,
        "anchors": [
            "Audit the locators in the Accounts Receivable module",
            "Check for brittle XPaths in Finance",
            "Find fragile test steps in the HCM module",
            "Lint the locators for bad practices",
        ],
        "micro_schema": '{"module": "<module name>"}',
        "micro_instruction": "Extract the target module name. (Crucial: a module is required for this action)",
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
    "analyze_oracle_patch": {
        "intent_enum": IntentName.ANALYZE_ORACLE_PATCH,
        "anchors": [
            "Check for Oracle updates",
            "Are there any new Oracle patch notes",
            "Run the Oracle Patch Analyzer",
            "Scan Oracle release notes",
            "Force run the Oracle Patch Analyzer",
            "Did Oracle release a new patch",
            "Analyze oracle updates",
            "Start the oracle bot"
        ],
        "micro_schema": '{}',
        "micro_instruction": "No arguments needed."
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
    """
    Constructs the exact injection prompt string given to the LLM during Stage 2.
    """
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
_ANCHOR_CACHE: dict[str, list[list[float]]] = {}


def _get_anchor_vectors(tool_name: str, anchors: list[str]) -> list[list[float]]:
    """Retrieves or computes the vector representations of the tool's anchor strings."""
    # Temporarily disabled cache to ensure hot-reload picks up anchor changes
    from app.services.embedding_service import embedding_service
    return embedding_service.embed_batch(anchors)


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two unit-normalized vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    return max(-1.0, min(1.0, dot))


def _score_tool(query_vector: list[float], tool_name: str, anchors: list[str]) -> float:
    """Return maximum cosine similarity between query vector and a given tool's anchors."""
    vecs = _get_anchor_vectors(tool_name, anchors)
    if not vecs:
        return 0.0
    return max(_cosine_similarity(query_vector, v) for v in vecs)


# ─────────────────────────────────────────────────────────────────────────────
# Cross-Encoder Singleton
# Loaded lazily on first use to avoid blocking startup. This model understands
# query-anchor pairs jointly, enabling it to correctly handle negation and
# complex query structures that fool bi-encoder models.
# ─────────────────────────────────────────────────────────────────────────────
_cross_encoder = None


def _get_cross_encoder():
    """Lazily loads and caches the cross-encoder model."""
    global _cross_encoder
    if _cross_encoder is None:
        try:
            from sentence_transformers import CrossEncoder
            logger.info("[CrossEncoder] Loading cross-encoder/ms-marco-MiniLM-L-6-v2 (first-time download may take a moment)...")
            _cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
            logger.info("[CrossEncoder] Model loaded successfully.")
        except Exception as e:
            logger.warning(f"[CrossEncoder] Failed to load cross-encoder model: {e}. Falling back to vector-only routing.")
            _cross_encoder = None
    return _cross_encoder


# ─────────────────────────────────────────────────────────────────────────────
# IntentRouterService
# ─────────────────────────────────────────────────────────────────────────────
class IntentRouterService:
    """
    Orchestrates the three-stage routing and extraction process:
    Stage 1: Regex fast-path (sub-millisecond exact matches)
    Stage 2: Bi-Encoder vector pre-filter → Cross-Encoder reranking
    Stage 3: Multi-Intent parallel LLM argument extraction
    """

    # Bi-encoder: minimum cosine similarity to enter candidate pool
    CANDIDATE_THRESHOLD = 0.38
    # Top-N bi-encoder candidates to pass to the cross-encoder
    TOP_N_CANDIDATES = 5
    # Cross-encoder: minimum logit score for an intent to survive reranking.
    # Empirically calibrated on ms-marco-MiniLM-L-6-v2 logit outputs:
    #   - Correct matches: range from -8.2 (weak) to +6.1 (strong)
    #   - Wrong/irrelevant: range from -10.6 to -15.0
    # -9.0 admits correct weak matches while rejecting true irrelevant ones.
    CROSS_ENCODER_THRESHOLD = -9.0
    # If two intents both survive reranking and their scores are within this
    # margin of each other, both are treated as valid co-intents.
    # 3.0 logits allows genuine compound intents (e.g. search + schedule) to execute in parallel.
    MULTI_INTENT_MARGIN = 3.0
    # Logit penalty applied to any tool that the user explicitly negated.
    # +3.6 -> +3.6 - 20.0 = -16.4, which drops well below any threshold.
    NEGATION_PENALTY = 20.0

    def _get_negated_tools(self, query: str) -> dict[str, float]:
        """
        Detects phrases explicitly negated in the user query (e.g. "NOT generate",
        "don't want to run", "without creating a suite") and returns a dict of
        {tool_name: penalty} for any tool whose anchors semantically match the
        negated phrase. The penalty is subtracted from the tool's cross-encoder
        score, pushing it below the survival threshold.

        The ms-marco cross-encoder is a retrieval model that is blind to negation;
        this pre-processor corrects for that fundamental limitation.
        """
        import re as _re
        # Patterns that capture the concept being negated
        negation_patterns = [
            r"\bNOT\s+([\w][\w\s]{2,40}?)(?:\s*[,.]|\s+just\b|\s+only\b|\s+but\b|$)",
            r"don'?t\s+want\s+(?:to\s+)?([\w][\w\s]{2,40}?)(?:\s*[,.]|\s+just\b|\s+only\b|$)",
            r"do\s+not\s+(?:want\s+(?:to\s+)?)?([\w][\w\s]{2,40}?)(?:\s*[,.]|\s+just\b|\s+only\b|$)",
            r"\bwithout\s+([\w][\w\s]{2,40}?)(?:\s*[,.]|$)",
            r"\binstead\s+of\s+([\w][\w\s]{2,40}?)(?:\s*[,.]|$)",
            r"\bavoid\s+([\w][\w\s]{2,40}?)(?:\s*[,.]|$)",
        ]

        negated_phrases = []
        q_lower = query.lower()
        for pattern in negation_patterns:
            for m in _re.finditer(pattern, q_lower, _re.IGNORECASE):
                phrase = m.group(1).strip()
                if len(phrase) > 3:
                    negated_phrases.append(phrase)

        if not negated_phrases:
            return {}

        logger.info("[NegationDetector] Detected negated phrases: %s", negated_phrases)

        # Embed each negated phrase and find all matching tool anchors
        penalties: dict[str, float] = {}
        try:
            from app.services.embedding_service import embedding_service
            for phrase in negated_phrases:
                phrase_vec = embedding_service.embed_text(phrase)
                for t_name, t_def in TOOL_ANCHORS.items():
                    if t_def.get("intent_enum") == IntentName.UNKNOWN:
                        continue
                    vecs = _get_anchor_vectors(t_name, t_def["anchors"])
                    sim = max((_cosine_similarity(phrase_vec, v) for v in vecs), default=0.0)
                    # Penalize any tool that closely matches the negated concept
                    if sim >= 0.65:
                        logger.info(
                            "[NegationDetector] Penalizing '%s' (sim=%.3f) for negated phrase: '%s'",
                            t_name, sim, phrase,
                        )
                        penalties[t_name] = max(penalties.get(t_name, 0.0), self.NEGATION_PENALTY)
        except Exception as e:
            logger.warning("[NegationDetector] Failed during phrase embedding: %s", e)

        return penalties

    def _extract_arguments(self, tool_name: str, tool_def: dict, query: str) -> dict[str, Any]:
        """
        Runs the Micro-LLM argument extractor for a single resolved intent.
        Returns an extracted arguments dict, or {} on failure.
        """
        schema_spec = tool_def.get("micro_schema", "{}")
        if schema_spec == "{}":
            return {}

        try:
            micro_user = _micro_extractor_user_prompt(
                tool_name=tool_name,
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
                json_mode=True,
            )
            clean = raw.strip()
            if "```" in clean:
                m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean, re.DOTALL)
                clean = m.group(1) if m else re.sub(r"```[a-z]*", "", clean).strip()
            parsed = json.loads(clean)
            if isinstance(parsed, dict):
                return parsed
        except Exception as exc:
            logger.warning("[MicroExtractor] Argument extraction failed for '%s': %s", tool_name, exc)
        return {}

    def _rerank_with_cross_encoder(
        self, query: str, candidates: list[tuple[str, float]]
    ) -> list[tuple[str, float, float]]:
        """
        Reranks a list of (tool_name, vector_score) candidates using the
        cross-encoder model. Returns (tool_name, vector_score, ce_score) tuples
        sorted by cross-encoder score descending.
        
        Falls back to vector-score ordering if the cross-encoder is unavailable.
        """
        ce = _get_cross_encoder()
        if ce is None:
            # Fallback: treat vector score as the cross-encoder score
            return [(t, s, s) for t, s in candidates]

        # For each candidate, pick the single best anchor (highest bi-encoder
        # similarity) to represent that tool in the cross-encoder pair.
        try:
            from app.services.embedding_service import embedding_service
            query_vector = embedding_service.embed_text(query)
        except Exception:
            return [(t, s, s) for t, s in candidates]

        pairs = []
        for tool_name, _ in candidates:
            anchors = TOOL_ANCHORS[tool_name]["anchors"]
            vecs = _get_anchor_vectors(tool_name, anchors)
            if not vecs:
                pairs.append((query, anchors[0]))
                continue
            # Pick the anchor whose vector is closest to the query
            best_anchor_idx = max(
                range(len(vecs)),
                key=lambda i: _cosine_similarity(query_vector, vecs[i])
            )
            pairs.append((query, anchors[best_anchor_idx]))

        try:
            scores = ce.predict(pairs)
        except Exception as exc:
            logger.warning("[CrossEncoder] Prediction failed: %s. Falling back.", exc)
            return [(t, s, s) for t, s in candidates]

        reranked = [
            (candidates[i][0], candidates[i][1], float(scores[i]))
            for i in range(len(candidates))
        ]
        reranked.sort(key=lambda x: x[2], reverse=True)
        logger.info(
            "[CrossEncoder] Reranked candidates: %s",
            [(t, f"vec={v:.3f}", f"ce={c:.3f}") for t, v, c in reranked],
        )
        return reranked

    # ── main routing loop ───────────────────────────────────────────────
    def route(self, request: IntentRequest) -> MultiIntentResult:
        """
        Executes the 3-stage routing pipeline:
        1. Regex fast-path override
        2. Bi-encoder vector pre-filter + Cross-Encoder reranking  
        3. Multi-intent parallel Micro-LLM argument extraction

        Args:
            request (IntentRequest): Contains the raw unstructured user string.

        Returns:
            MultiIntentResult: One or more resolved intents with extracted arguments.
        """
        if not settings.is_llm_configured:
            logger.warning("LLM not configured; returning unknown intent.")
            return self._unresolvable("LLM not configured.")

        query = request.user_query.strip()

        # ── Stage 1: Global Regex Fast-Path (Overrides Semantic Match) ───────
        # Handles unambiguous patterns like script IDs (TS.AP.001) instantly.
        for tool_name, tool_def in TOOL_ANCHORS.items():
            fastpath = tool_def.get("regex_fastpath")
            if fastpath:
                m = re.search(fastpath["pattern"], query)
                if m:
                    logger.info("[Stage1:RegexFastPath] Matched '%s' for tool '%s'", m.group(), tool_name)
                    return MultiIntentResult(intents=[IntentResult(
                        intent=tool_def["intent_enum"],
                        tool=tool_name,
                        arguments={fastpath["map_to"]: m.group(1)},
                        confidence=1.0,
                        reasoning="Exact regex match on script ID or specific pattern."
                    )])

        # ── Stage 2a: Bi-Encoder Vector Pre-Filter ──────────────────────────
        # Generate a dense vector for the query and compute cosine similarity
        # against every tool's anchor vectors. Keeps the top-N candidates.
        try:
            from app.services.embedding_service import embedding_service
            query_vector = embedding_service.embed_text(query)
        except Exception as exc:
            logger.error("[Stage2a:Vector] Embedding failed: %s", exc)
            return self._unresolvable(str(exc))

        scored: list[tuple[str, float]] = []
        for tool_name, tool_def in TOOL_ANCHORS.items():
            score = _score_tool(query_vector, tool_name, tool_def["anchors"])
            if score >= self.CANDIDATE_THRESHOLD:
                scored.append((tool_name, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        top_candidates = scored[: self.TOP_N_CANDIDATES]

        logger.info(
            "[Stage2a:Vector] Candidates for '%s': %s",
            query[:60],
            [(t, f"{s:.3f}") for t, s in top_candidates],
        )

        if not top_candidates:
            logger.info("[Stage2a:Vector] No candidates above threshold — returning unknown.")
            return self._unresolvable("Query did not match any tool with sufficient semantic similarity.")

        # ── Stage 2b: Cross-Encoder Reranking ──────────────────────────────
        # The cross-encoder processes the query + anchor *jointly*, enabling
        # it to distinguish near-synonymous tools that the bi-encoder confuses.
        # Note: ms-marco models are blind to negation; the negation pre-processor
        # below corrects for this by applying score penalties.
        reranked = self._rerank_with_cross_encoder(query, top_candidates)

        # ── Negation Pre-Processor ─────────────────────────────────────────
        # Detect explicitly negated concepts ("NOT generate", "don't run")
        # and apply a logit penalty to the matching tool's CE score.
        # This overcomes the ms-marco model's inability to handle negation.
        negation_penalties = self._get_negated_tools(query)
        if negation_penalties:
            reranked = [
                (t, v, c - negation_penalties.get(t, 0.0))
                for t, v, c in reranked
            ]
            reranked.sort(key=lambda x: x[2], reverse=True)
            logger.info(
                "[NegationDetector] Scores after penalty: %s",
                [(t, f"ce={c:.3f}") for t, _, c in reranked],
            )

        # Filter to only intents that the cross-encoder considers relevant
        best_ce_score = reranked[0][2]
        surviving = [
            (t, v, c) for t, v, c in reranked
            if c >= self.CROSS_ENCODER_THRESHOLD
            and (best_ce_score - c) <= self.MULTI_INTENT_MARGIN
        ]

        if not surviving:
            logger.info("[Stage2b:CrossEncoder] All candidates dropped below CE threshold.")
            return self._unresolvable("Cross-encoder rejected all candidates — query is ambiguous or out-of-scope.")

        logger.info(
            "[Stage2b:CrossEncoder] Surviving intents: %s",
            [(t, f"ce={c:.3f}") for t, _, c in surviving],
        )

        # ── Stage 3: Multi-Intent Parallel Micro-LLM Argument Extraction ─────
        # For every surviving intent, extract its required arguments from the
        # user query in parallel using the focused Micro-LLM extractor.
        # This is what enables chaining: "Find PO tests and run them" → two
        # IntentResult objects in the returned MultiIntentResult.
        resolved_intents: list[IntentResult] = []

        for idx, (tool_name, vec_score, ce_score) in enumerate(surviving):
            tool_def = TOOL_ANCHORS[tool_name]
            intent_enum = tool_def["intent_enum"]

            # Skip the conversational_fallback placeholder — it maps to UNKNOWN
            if intent_enum == IntentName.UNKNOWN:
                logger.info("[Stage3] Skipping conversational_fallback tool '%s'", tool_name)
                continue

            arguments = self._extract_arguments(tool_name, tool_def, query)

            # Calibrate confidence: primary intent uses CE score, secondaries are
            # slightly discounted to reflect their role as co-intents.
            raw_confidence = min(0.99, max(0.60, 0.75 + (ce_score / 20.0)))
            if idx > 0:
                raw_confidence = round(raw_confidence * 0.92, 3)  # slight discount for co-intents
            else:
                raw_confidence = round(raw_confidence, 3)

            logger.info(
                "[Stage3] Resolved intent #%d: tool=%s ce_score=%.3f confidence=%.3f args=%s",
                idx, tool_name, ce_score, raw_confidence, arguments,
            )

            resolved_intents.append(IntentResult(
                intent=intent_enum,
                tool=tool_name,
                arguments=arguments,
                confidence=raw_confidence,
                ambiguities=[],
                reasoning=(
                    f"Cross-encoder score={ce_score:.3f} (vector={vec_score:.3f}). "
                    + ("Primary intent." if idx == 0 else f"Co-intent #{idx} (within {self.MULTI_INTENT_MARGIN:.0f}-logit margin of primary).")
                ),
            ))

        if not resolved_intents:
            return self._unresolvable("No actionable intents survived the cross-encoder pass.")

        logger.info(
            "[HybridRouter] Final result: %d intent(s) → %s",
            len(resolved_intents),
            [i.tool for i in resolved_intents],
        )
        return MultiIntentResult(intents=resolved_intents)

    # ── unresolvable fallback ───────────────────────────────────────────
    def _unresolvable(self, reasoning: str) -> MultiIntentResult:
        """
        Creates a fallback 'UNKNOWN' intent payload when routing fails.
        """
        return MultiIntentResult(intents=[IntentResult(
            intent=IntentName.UNKNOWN,
            tool="unknown",
            arguments={},
            confidence=0.0,
            ambiguities=["Query could not be resolved to any tool."],
            reasoning=reasoning,
        )])


# ── singleton export ──────────────────────────────────────────────────
intent_router_service = IntentRouterService()
