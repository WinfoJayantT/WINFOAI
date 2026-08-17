import logging
import time
import json
import os
from typing import Any, Dict, List, Optional

from app.clients.llm_client import llm_client
from app.repositories.test_script_repository import test_script_repository
from app.schemas.test_suite import (
    CoverageGapItem,
    TestSuiteRequest,
    TestSuiteResponse,
    TestSuiteStepItem,
)
from app.services.conversation_state_service import conversation_state_service
from app.services.debug_trace_service import debug_trace_service

logger = logging.getLogger(__name__)


class TestSuiteService:
    """Generates structured E2E regression test suites and detects ERP business process coverage gaps."""
    
    def _load_mbp_mappings(self) -> List[Dict[str, Any]]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'oracle_mbp_mappings.json')
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load MBP mappings: {e}")
            return []

    def generate_suite(
        self, request: TestSuiteRequest, session_id: str = "default"
    ) -> Dict[str, Any]:
        start_time = time.time()
        logger.info(f"Generating test suite for request: {request} in session: {session_id}")
        
        PROCESS_MAPPINGS = self._load_mbp_mappings()

        # Retrieve all test scripts from PostgreSQL source of truth
        all_scripts = test_script_repository.list_all()
        if not all_scripts:
            return {
                "status": "not_found",
                "message": "No test scripts available in the database to compose a test suite.",
                "total_scripts": 0,
            }

        target_area = (request.process_area or request.process_flow or request.target_module or "Procure to Pay").strip()

        # Filter relevant MBP process mappings
        matching_mappings = [
            m for m in PROCESS_MAPPINGS
            if target_area.lower() in m["l1_process"].lower()
            or target_area.lower() in m["l2_process"].lower()
            or any(w in m["l1_process"].lower() for w in target_area.lower().split() if len(w) > 3)
        ]

        if not matching_mappings:
            matching_mappings = PROCESS_MAPPINGS[:10]

        # Filter scripts that belong to or align with this process
        relevant_scripts = []
        for s in all_scripts:
            name_desc = f"{s.get('script_name', '')} {s.get('test_script_number', '')} {s.get('module', '')} {s.get('process_area', '')} {s.get('process', '')} {s.get('description', '')}".lower()
            if any(w in name_desc for w in target_area.lower().split() if len(w) > 2):
                relevant_scripts.append(s)

        if not relevant_scripts:
            # Fallback to first batch of domain scripts
            relevant_scripts = all_scripts[:5]

        # Order scripts logically into sequential workflow steps
        execution_steps: List[TestSuiteStepItem] = []
        selected_script_ids: List[str] = []

        for idx, script in enumerate(relevant_scripts[:25], start=1):
            s_id = str(script.get("id") or script.get("test_script_number"))
            selected_script_ids.append(s_id)
            execution_steps.append(
                TestSuiteStepItem(
                    step_sequence=idx,
                    test_script_number=script.get("test_script_number", f"TS-{idx:03d}"),
                    script_name=script.get("script_name") or script.get("name") or "Unnamed Script",
                    process_name=script.get("process") or script.get("process_area"),
                    module=script.get("module"),
                    business_role=script.get("role") or "Automation Engineer",
                    step_objective=script.get("objective") or script.get("description") or f"Execute end-to-end stage {idx} for {script.get('script_name')}",
                    estimated_duration_mins=round(1.5 + (idx * 0.5), 1),
                )
            )

        # Detect coverage gaps from MBP mappings
        coverage_gaps: List[CoverageGapItem] = []
        for mapping in matching_mappings:
            if not mapping.get("is_covered", True):
                coverage_gaps.append(
                    CoverageGapItem(
                        process_stage=f"{mapping['l1_process']} → {mapping['l2_process']}",
                        missing_capability=f"Automated test coverage for '{mapping['l2_process']}' is not yet provisioned in the repository.",
                        risk_level="HIGH" if "Close" in mapping["l2_process"] or "Tax" in mapping["l2_process"] else "MEDIUM",
                        recommendation=f"Author test script covering {mapping['l2_process']} to achieve 100% ERP business compliance.",
                    )
                )

        if not coverage_gaps:
            coverage_gaps.append(
                CoverageGapItem(
                    process_stage=f"{target_area} Exception Handling",
                    missing_capability="Negative boundary validation and edge-case rollback tests.",
                    risk_level="LOW",
                    recommendation="Add negative test scripts verifying approval rejection paths.",
                )
            )

        total_duration = sum(step.estimated_duration_mins for step in execution_steps)

        # Save selected script IDs to conversation state for immediate follow-up execution
        state = conversation_state_service.get(session_id)
        state.last_result_label = f"Generated test suite for '{target_area}'"
        state.last_result_script_ids = selected_script_ids
        state.can_execute_previous_result = len(selected_script_ids) > 0
        conversation_state_service.save(state)

        trace = debug_trace_service.build_trace(
            intent="generate_test_suite",
            tool_name="generate_test_suite",
            parsed_args=request.model_dump(),
            repo_path="test_script_repository.list_all -> process_mappings",
            execution_time_ms=int((time.time() - start_time) * 1000),
            warnings=[] if execution_steps else ["No direct script matches found; generalized flow used."],
        )

        response = TestSuiteResponse(
            status="success",
            suite_name=f"E2E Automated Regression: {target_area}",
            process_area=target_area,
            suite_description=f"End-to-end regression validation pipeline composed of {len(execution_steps)} sequential test stages covering {target_area}.",
            total_scripts=len(execution_steps),
            estimated_total_duration_mins=round(total_duration, 1),
            execution_steps=execution_steps,
            coverage_gaps=coverage_gaps,
            reasoning=f"Identified {len(execution_steps)} relevant test scripts and cross-referenced {len(matching_mappings)} Oracle MBP process stages to assemble an executable flow.",
            debug_trace=trace.to_dict(),
        )
        return response.model_dump()


test_suite_service = TestSuiteService()
