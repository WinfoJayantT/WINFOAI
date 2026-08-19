"""
WinfoTest AI Tool Registry Service
==================================

This module orchestrates the entire AI backend execution pipeline.
It acts as the central traffic cop, receiving incoming chat requests, querying the
`IntentRouterService` to determine the user's intent, dispatching the request to the
appropriate domain service, logging audit telemetry, and formatting the output stream.
"""

import logging
import time
from typing import Any, Dict, Generator, Optional
import json

from app.repositories.audit_repository import audit_repository
from app.schemas.cluster import ClusterRequest
from app.schemas.intent import IntentRequest, IntentResult, IntentName, MultiIntentResult
from app.schemas.test_risk import RiskAssessmentRequest
from app.schemas.test_suite import TestSuiteRequest
from app.services.intent_router_service import intent_router_service
from app.services.semantic_cluster_service import semantic_cluster_service
from app.services.semantic_search_service import semantic_search_service
from app.services.script_analysis_service import script_analysis_service
from app.services.failure_analysis_service import failure_analysis_service
from app.services.execution_orchestration_service import execution_orchestration_service
from app.services.test_suite_service import test_suite_service
from app.services.risk_assessment_service import risk_assessment_service
from app.services.step_generation_service import step_generation_service
from app.clients.llm_client import llm_client

# ── logger initialization ───────────────────────────────────────────────
logger = logging.getLogger(__name__)


# ── class definition ──────────────────────────────────────────────────
class ToolRegistryService:
    """
    Core Orchestrator for mapping user intents to concrete backend service execution.
    
    Responsibilities:
      - Intent dispatch via `IntentRouterService`.
      - Safe execution of underlying tools with unified error handling.
      - Asynchronous Server-Sent Events (SSE) streaming for real-time frontend UI feedback.
      - Comprehensive database auditing for analytics.
    """

    # ── streaming chat dispatch ─────────────────────────────────────────
    async def stream_chat(
        self, user_query: str, session_id: str = "default", test_data: Optional[Dict[str, Any]] = None
    ) -> Generator[str, None, None]:
        """
        Processes a chat query and yields an SSE stream of status tokens and the final JSON payload.
        
        Args:
            user_query (str): The raw text input from the user.
            session_id (str): Optional UUID for tracking multi-turn conversation state.
            test_data (Dict): Optional contextual testing parameters attached from the frontend.
            
        Yields:
            str: SSE formatted chunks (e.g. `data: {"type": "token", "content": "..."}\\n\\n`)
        """
        start_time = time.time()
        logger.info(f"Streaming chat query: '{user_query}' for session: {session_id}")

        try:
            # 1. Resolve Intent
            intent_request = IntentRequest(user_query=user_query)
            route_result: MultiIntentResult = intent_router_service.route(intent_request)

            tool_results = []
            ambiguous_intents = []
            
            # 2. Iterate and Execute Resolved Intents
            for intent_res in route_result.intents:
                logger.info(
                    f"Routed intent: {intent_res.intent} -> tool: {intent_res.tool} (Confidence: {intent_res.confidence})"
                )
                
                # Check confidence thresholding
                if intent_res.confidence < 0.70 or intent_res.tool == "unknown" or intent_res.intent == IntentName.UNKNOWN:
                    ambiguous_intents.append(intent_res)
                    continue
                    
                args_to_pass = dict(intent_res.arguments)
                if test_data:
                    args_to_pass["test_data"] = test_data

                # Execute target service tool
                res = self.execute_tool(
                    intent_res.tool, args_to_pass, session_id=session_id
                )
                if isinstance(res, dict):
                    res.setdefault("tool", intent_res.tool)
                
                tool_results.append(res)
                
                # 3. Log execution telemetry asynchronously
                duration_ms = int((time.time() - start_time) * 1000)
                rec_count = len(res.get("execution_steps", [])) or len(res.get("matches", [])) or len(res.get("risk_items", [])) or 1
                audit_repository.log_execution(
                    tool_name=intent_res.tool,
                    intent=str(intent_res.intent),
                    arguments_json=intent_res.arguments,
                    status=res.get("status", "success"),
                    records_returned=rec_count,
                    duration_ms=duration_ms,
                    session_id=session_id,
                )
                
            # 4. Handle Ambiguous Queries
            if ambiguous_intents and not tool_results:
                ambiguous_res = {
                    "status": "ambiguous",
                    "tool": "unknown",
                    "message": "Your query is too broad or ambiguous. Please clarify.",
                    "clarification_options": [
                        "Generate an E2E Test Suite (e.g., Procure to Pay)",
                        "Assess Test Risks & Flakiness",
                        "Recommend Self-Healing Locator Fixes",
                        "Group scripts by Process Area",
                    ],
                    "reasoning": "Confidence score is below threshold or intent is unknown."
                }
                yield f'data: {{"type": "token", "content": "I wasn\'t quite sure what you meant by that. Could you clarify? For example, you can ask me to generate a test suite, search for specific tests, or group tests by process area."}}\n\n'
                yield f'data: {{"type": "done", "results": [{json.dumps(ambiguous_res, default=str)}]}}\n\n'
                return

            if not tool_results:
                yield f'data: {{"type": "token", "content": "I couldn\'t find any specific actions to take based on your request."}}\n\n'
                yield f'data: {{"type": "done", "results": []}}\n\n'
                return

            # 5. Emit successful final result payload back to UI
            final_payload = json.dumps({"type": "done", "results": tool_results}, default=str)
            yield f'data: {final_payload}\n\n'

        except Exception as exc:
            logger.error(f"Error handling chat request: {exc}")
            err_res = {
                "status": "internal_error",
                "tool": "unknown",
                "message": "An internal system error occurred.",
                "reasoning": str(exc),
            }
            yield f'data: {{"type": "token", "content": "An internal error occurred while processing your request."}}\n\n'
            yield f'data: {{"type": "done", "results": [{json.dumps(err_res, default=str)}]}}\n\n'


    # ── synchronous chat dispatch ───────────────────────────────────────
    def handle_chat(
        self, user_query: str, session_id: str = "default"
    ) -> Dict[str, Any]:
        """
        Synchronous fallback for processing chat requests. 
        Functions identically to `stream_chat` but blocks until the entire payload is ready.
        """
        start_time = time.time()
        logger.info(f"Handling chat query: '{user_query}' for session: {session_id}")

        try:
            intent_request = IntentRequest(user_query=user_query)
            multi_route = intent_router_service.route(intent_request)
            route_result: IntentResult = multi_route.primary_intent

            logger.info(
                f"Routed intent: {route_result.intent} -> tool: {route_result.tool} (Confidence: {route_result.confidence})"
            )

            # Confidence Thresholding
            if route_result.confidence < 0.70 or route_result.tool == "unknown" or route_result.intent == IntentName.UNKNOWN:
                ambiguous_res = {
                    "status": "ambiguous",
                    "tool": "unknown",
                    "message": "Your query is too broad or ambiguous. How would you like to proceed?",
                    "clarification_options": [
                        "Generate an E2E Test Suite (e.g., Procure to Pay)",
                        "Assess Test Risks & Flakiness",
                        "Recommend Self-Healing Locator Fixes",
                        "Group scripts by Process Area",
                    ],
                    "reasoning": "Confidence score is below threshold or intent is unknown."
                }
                audit_repository.log_execution(
                    tool_name="unknown",
                    intent=str(route_result.intent),
                    arguments_json={},
                    status="ambiguous",
                    records_returned=0,
                    duration_ms=int((time.time() - start_time) * 1000),
                    session_id=session_id,
                )
                return ambiguous_res

            res = self.execute_tool(
                route_result.tool, route_result.arguments, session_id=session_id
            )
            if isinstance(res, dict):
                res.setdefault("tool", route_result.tool)

            duration_ms = int((time.time() - start_time) * 1000)
            rec_count = len(res.get("execution_steps", [])) or len(res.get("matches", [])) or len(res.get("risk_items", [])) or 1
            audit_repository.log_execution(
                tool_name=route_result.tool,
                intent=str(route_result.intent),
                arguments_json=route_result.arguments,
                status=res.get("status", "success"),
                records_returned=rec_count,
                duration_ms=duration_ms,
                session_id=session_id,
            )
            return res
        except Exception as exc:
            logger.error(f"Error handling chat request: {exc}")
            audit_repository.log_execution(
                tool_name="unknown",
                status="error",
                error_message=str(exc),
                duration_ms=int((time.time() - start_time) * 1000),
                session_id=session_id,
            )
            return {
                "status": "internal_error",
                "tool": "unknown",
                "message": "An internal system error occurred.",
                "reasoning": str(exc),
            }


    # ── backend tool execution mapping ──────────────────────────────────
    def execute_tool(
        self, tool_name: str, arguments: Dict[str, Any], session_id: str = "default"
    ) -> Dict[str, Any]:
        """
        Maps a resolved tool name string directly to its corresponding Domain Service.
        Extracts expected arguments from the dynamic JSON and fires the backend logic.
        
        Args:
            tool_name (str): The registered name of the tool (e.g. 'generate_script_steps')
            arguments (Dict): The parameters extracted by the LLM (e.g. '{"scenario": "..."}')
            session_id (str): Identifies the user session state.
        
        Returns:
            Dict: The structured output payload generated by the backend service.
        """
        logger.info(f"Executing tool '{tool_name}' with arguments: {arguments}")

        try:
            if tool_name == "semantic_cluster_scripts":
                concept = arguments.get("concept", "general")
                filter_query = arguments.get("filter_query")
                req = ClusterRequest(concept=concept, filter_query=filter_query)
                return semantic_cluster_service.cluster(req, session_id=session_id)

            elif tool_name == "semantic_search_tests":
                query = arguments.get("query", "")
                # Enforce minimum 8 results — LLM micro-extractor may under-estimate limit
                limit = max(8, int(arguments.get("limit", 8)))
                # Steps are never fetched for a plain search — user must explicitly ask
                include_steps = False
                filters = arguments.get("filters")
                return semantic_search_service.search(
                    query, limit=limit, include_steps=include_steps, filters=filters
                )

            elif tool_name == "filtered_script_lookup":
                identifier = arguments.get("identifier", "")
                return script_analysis_service.lookup_script(identifier)

            elif tool_name == "analyze_entity":
                identifier = arguments.get("identifier", "")
                error_log_val = arguments.get("error_log") or arguments.get("error") or arguments.get("log") or ""
                if error_log_val:
                    return failure_analysis_service.analyze_failure(
                        error_log=error_log_val, script_name=identifier
                    )
                return script_analysis_service.analyze(identifier)

            elif tool_name == "generate_test_suite":
                process_area = arguments.get("process_area") or arguments.get("process_flow")
                target_module = arguments.get("target_module")
                req = TestSuiteRequest(process_area=process_area, target_module=target_module)
                return test_suite_service.generate_suite(req, session_id=session_id)

            elif tool_name == "recommend_locator_fixes":
                script_name = arguments.get("script_name") or arguments.get("identifier")
                error_log = arguments.get("error_log") or arguments.get("error")
                return failure_analysis_service.recommend_locator_repairs(
                    script_name=script_name, error_log=error_log
                )

            elif tool_name == "assess_test_risk":
                filter_query = arguments.get("filter_query") or arguments.get("concept")
                min_risk = arguments.get("min_risk_level", "ALL")
                req = RiskAssessmentRequest(filter_query=filter_query, min_risk_level=min_risk)
                return risk_assessment_service.assess_risk(req, session_id=session_id)

            elif tool_name == "execute_script_set":
                return execution_orchestration_service.execute_previous_result(
                    session_id=session_id
                )
                
            elif tool_name == "index_all_scripts":
                from app.services.indexing_service import indexing_service
                fast_mode = bool(arguments.get("fast_mode", True))
                return indexing_service.trigger_asynchronous_index(fast_mode=fast_mode)

            elif tool_name == "check_indexing_status":
                from app.services.indexing_service import indexing_service
                status_info = indexing_service.get_status()
                return {
                    "status": "success",
                    "is_indexing": status_info["is_indexing"],
                    "processed_scripts": status_info["processed_scripts"],
                    "total_scripts": status_info["total_scripts"],
                    "message": "Indexing is currently running." if status_info["is_indexing"] else "Indexing is idle.",
                }

            elif tool_name == "generate_script_steps":
                scenario = arguments.get("scenario") or arguments.get("description") or arguments.get("query", "")
                process_area = arguments.get("process_area") or arguments.get("process") or ""
                test_data = arguments.get("test_data")
                return step_generation_service.generate_steps(
                    scenario=scenario, process_area=process_area, test_data=test_data
                )

            else:
                return {
                    "status": "not_found", 
                    "tool": tool_name, 
                    "message": f"Tool '{tool_name}' is not recognized."
                }
        except Exception as exc:
            logger.error(f"Tool execution error for '{tool_name}': {exc}")
            return {
                "status": "internal_error",
                "tool": tool_name,
                "message": "The backend tool encountered an error during execution.",
                "reasoning": str(exc),
            }


# ── singleton export ──────────────────────────────────────────────────
tool_registry_service = ToolRegistryService()
