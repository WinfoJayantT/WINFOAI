"""
WinfoTest AI Tool Registry Service
==================================

This module orchestrates the entire AI backend execution pipeline.
It acts as the central traffic cop, receiving incoming chat requests, querying the
`IntentRouterService` to determine the user's intent, dispatching the request to the
appropriate domain service, logging audit telemetry, and formatting the output stream.
"""

import asyncio
import json
import logging
import time
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from app.repositories.audit_repository import audit_repository
from app.schemas.cluster import ClusterRequest
from app.schemas.intent import (
    IntentName,
    IntentRequest,
    MultiIntentResult,
)
from app.schemas.test_risk import RiskAssessmentRequest
from app.schemas.test_suite import TestSuiteRequest
from app.services.execution_orchestration_service import execution_orchestration_service
from app.services.failure_analysis_service import failure_analysis_service
from app.services.intent_router_service import intent_router_service
from app.services.risk_assessment_service import risk_assessment_service
from app.services.script_analysis_service import script_analysis_service
from app.services.semantic_cluster_service import semantic_cluster_service
from app.services.semantic_search_service import semantic_search_service
from app.services.step_generation_service import step_generation_service
from app.services.test_suite_service import test_suite_service

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
        self, user_query: str, session_id: str = "default", test_data: dict[str, Any] | None = None, active_context: dict[str, Any] | None = None, low_memory_mode: bool = False
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
            import uuid

            from app.models.orm import AiChatMessage, AiConversationSession
            from app.repositories.db import SessionLocal
            
            # Save user query to history
            try:
                db = SessionLocal()
                
                # Ensure the session exists in the DB to satisfy foreign key constraint
                session_obj = db.query(AiConversationSession).filter(AiConversationSession.session_id == session_id).first()
                if not session_obj:
                    session_obj = AiConversationSession(session_id=session_id)
                    db.add(session_obj)
                    db.commit()

                new_msg = AiChatMessage(
                    id=uuid.uuid4(),
                    session_id=session_id,
                    role="user",
                    content=user_query
                )
                db.add(new_msg)
                db.commit()
            except Exception as e:
                logger.error(f"Failed to save user message: {e}")
                
            # Fetch recent history for context
            conversation_context = None
            try:
                recent = db.query(AiChatMessage).filter(
                    AiChatMessage.session_id == session_id
                ).order_by(AiChatMessage.timestamp.desc()).limit(8).all()
                
                if recent:
                    recent.reverse()
                    conversation_context = {
                        "recent_messages": [
                            {"role": m.role, "content": m.content} for m in recent
                        ]
                    }
                db.close()
            except Exception as e:
                logger.error(f"Failed to fetch history: {e}")

            if active_context:
                if test_data is None:
                    test_data = {}
                test_data["active_context"] = active_context
                if active_context.get("type") == "script" and active_context.get("id"):
                    from app.repositories.test_script_repository import (
                        test_script_repository,
                    )
                    script_id = active_context.get("id")
                    full_script = test_script_repository.get_by_id(script_id)
                    if full_script:
                        test_data["active_script_details"] = full_script
                        logger.info(f"Injected active script context for {script_id}")

            # 1. Resolve Intent
            intent_request = IntentRequest(
                user_query=user_query, 
                conversation_context=conversation_context,
                app_context=test_data
            )
            # ── THINKING STEP 1: routing ───────────────────────────────────
            yield json.dumps({"type": "thinking_step", "stage": "routing", "message": "Analyzing query intent..."}) + "\n\n"
            yield ""  # flush

            route_result: MultiIntentResult = intent_router_service.route(intent_request)

            # ── THINKING STEP 2: tools resolved ───────────────────────────
            resolved_tools = [r.tool for r in route_result.intents if r.confidence >= 0.60]
            yield json.dumps({
                "type": "thinking_step",
                "stage": "tools_resolved",
                "tools": resolved_tools,
                "intent_count": len(resolved_tools),
                "message": f"Resolved {len(resolved_tools)} action(s): {', '.join(resolved_tools)}" if resolved_tools else "Ambiguous query detected.",
            }) + "\n\n"
            yield ""  # flush

            tool_results = []
            ambiguous_intents = []

            # 2. Parallel Execute Resolved Intents
            loop = asyncio.get_running_loop()

            async def _execute_and_log(intent_res):
                logger.info(
                    f"Routed intent: {intent_res.intent} -> tool: {intent_res.tool} (Confidence: {intent_res.confidence})"
                )
                
                # Check confidence thresholding (0.60 threshold aligns with Cross-Encoder survival)
                if intent_res.confidence < 0.60 or intent_res.tool == "unknown" or intent_res.intent == IntentName.UNKNOWN:
                    ambiguous_intents.append(intent_res)
                    return None
                    
                args_to_pass = dict(intent_res.arguments)
                if test_data:
                    args_to_pass["test_data"] = test_data

                # Execute target service tool concurrently in a thread
                executor = ThreadPoolExecutor(max_workers=2) if low_memory_mode else None
                res = await loop.run_in_executor(
                    executor, self.execute_tool, intent_res.tool, args_to_pass, session_id
                )
                if isinstance(res, dict):
                    res.setdefault("tool", intent_res.tool)
                
                # 3. Log execution telemetry asynchronously
                duration_ms = int((time.time() - start_time) * 1000)
                rec_count = len(res.get("execution_steps", [])) or len(res.get("matches", [])) or len(res.get("risk_items", [])) or 1
                
                await loop.run_in_executor(
                    None,
                    audit_repository.log_execution,
                    intent_res.tool,
                    str(intent_res.intent),
                    intent_res.arguments,
                    res.get("status", "success"),
                    rec_count,
                    duration_ms,
                    session_id
                )
                return res

            # ── THINKING STEP 3: executing ────────────────────────────────
            for ir in route_result.intents:
                if ir.confidence >= 0.60 and ir.tool != "unknown":
                    yield json.dumps({
                        "type": "thinking_step",
                        "stage": "executing",
                        "tool": ir.tool,
                        "confidence": round(ir.confidence, 2),
                        "message": f"Executing: {ir.tool} (confidence {round(ir.confidence * 100)}%)",
                    }) + "\n\n"
                    yield ""  # flush

            # Launch all intents concurrently
            tasks = [_execute_and_log(intent_res) for intent_res in route_result.intents]
            results = await asyncio.gather(*tasks)
            
            tool_results = [r for r in results if r is not None]
                
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
                yield 'data: {"type": "token", "content": "I wasn\'t quite sure what you meant by that. Could you clarify? For example, you can ask me to generate a test suite, search for specific tests, or group tests by process area."}\n\n'
                yield f'data: {{"type": "done", "results": [{json.dumps(ambiguous_res, default=str)}]}}\n\n'
                return

            if not tool_results:
                yield 'data: {"type": "token", "content": "I couldn\'t find any specific actions to take based on your request."}\n\n'
                yield 'data: {"type": "done", "results": []}\n\n'
                return

            # ── THINKING STEP 4: complete ─────────────────────────────────
            yield json.dumps({
                "type": "thinking_step",
                "stage": "complete",
                "tool_count": len(tool_results),
                "message": f"All {len(tool_results)} tool(s) complete. Rendering results...",
            }) + "\n\n"
            yield ""  # flush

            # 5. Emit successful final result payload back to UI
            final_payload = json.dumps({"type": "done", "results": tool_results}, default=str)
            yield f'data: {final_payload}\n\n'

            # Save assistant response to history
            try:
                db = SessionLocal()
                bot_msg = AiChatMessage(
                    id=uuid.uuid4(),
                    session_id=session_id,
                    role="assistant",
                    content=json.dumps([{"tool": r["tool"], "status": r.get("status")} for r in tool_results])
                )
                db.add(bot_msg)
                db.commit()
                db.close()
            except Exception as e:
                logger.error(f"Failed to save bot message: {e}")

        except Exception as exc:
            logger.exception("Unhandled error in stream_chat pipeline")
            err_res = {
                "status": "internal_error",
                "tool": "unknown",
                "message": "An internal system error occurred.",
                "reasoning": str(exc),
            }
            yield 'data: {"type": "token", "content": "An internal error occurred while processing your request."}\n\n'
            yield f'data: {{"type": "done", "results": [{json.dumps(err_res, default=str)}]}}\n\n'


    # ── synchronous chat dispatch ───────────────────────────────────────
    def handle_chat(self, user_query: str, session_id: str = "default", active_context: dict[str, Any] | None = None, low_memory_mode: bool = False) -> dict[str, Any]:
        """
        Synchronous wrapper around the stream_chat generator.
        Useful for standard REST endpoints that do not want to parse SSE.
        """
        final_result = None
        for chunk in self.stream_chat(user_query, session_id=session_id, active_context=active_context, low_memory_mode=low_memory_mode):
            if chunk.startswith("data: "):
                try:
                    payload = json.loads(chunk[6:].strip())
                    if payload.get("type") == "done":
                        results = payload.get("results", [])
                        if results:
                            final_result = results[0]
                except Exception:
                    pass
        return final_result or {"status": "error", "message": "No result generated"}


    # ── backend tool execution mapping ──────────────────────────────────
    def execute_tool(
        self, tool_name: str, arguments: dict[str, Any], session_id: str = "default"
    ) -> dict[str, Any]:
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
                
                # Fallback to active context if user is chatting about currently open script
                test_data = arguments.get("test_data")
                if not identifier and test_data and test_data.get("active_context"):
                    if test_data["active_context"].get("type") == "script":
                        identifier = test_data["active_context"].get("id", "")
                        
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

            elif tool_name == "schedule_test_run":
                from app.services.scheduling_service import scheduling_service
                target_suite = arguments.get("target_suite") or arguments.get("suite_name") or arguments.get("script_name") or arguments.get("target_name") or ""
                scheduled_time = arguments.get("scheduled_time") or ""
                return scheduling_service.schedule_run(target_suite=target_suite, scheduled_time=scheduled_time)

            elif tool_name == "analyze_test_results":
                from app.services.analytics_service import analytics_service
                timeframe = arguments.get("timeframe") or ""
                module = arguments.get("module") or ""
                status = arguments.get("status") or ""
                return analytics_service.analyze_results(timeframe=timeframe, module=module, status=status)

            elif tool_name == "detect_duplicates":
                from app.services.duplicate_detection_service import (
                    duplicate_detection_service,
                )
                module = arguments.get("module") or ""
                return duplicate_detection_service.detect_duplicates(module=module)
                
            elif tool_name == "lint_locators":
                from app.services.locator_linting_service import locator_linting_service
                module = arguments.get("module") or ""
                return locator_linting_service.lint_locators(module=module)

            elif tool_name == "analyze_oracle_patch":
                from app.services.oracle_patch_bot_service import (
                    oracle_patch_bot_service,
                )
                return oracle_patch_bot_service.analyze_oracle_patch_sync(arguments, session_id=session_id)

            else:
                return {
                    "status": "not_found", 
                    "tool": tool_name, 
                    "message": f"Tool '{tool_name}' is not recognized."
                }
        except Exception as exc:
            logger.exception("Unhandled error executing tool '%s'", tool_name)
            return {
                "status": "internal_error",
                "tool": tool_name,
                "message": "The backend tool encountered an error during execution.",
                "reasoning": str(exc),
            }


# ── singleton export ──────────────────────────────────────────────────
tool_registry_service = ToolRegistryService()
