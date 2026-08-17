import pytest
from unittest.mock import MagicMock, patch

from app.schemas.test_suite import TestSuiteRequest
from app.schemas.test_risk import RiskAssessmentRequest
from app.services.test_suite_service import test_suite_service
from app.services.risk_assessment_service import risk_assessment_service
from app.services.failure_analysis_service import failure_analysis_service
from app.services.audit_analytics_service import audit_analytics_service
from app.services.tool_registry_service import tool_registry_service


def test_test_suite_generation_service():
    mock_scripts = [
        {
            "id": "11111111-1111-1111-1111-111111111111",
            "test_script_number": "P2P-PO-0001",
            "script_name": "Create Purchase Order",
            "module": "PO",
            "process": "Manage Purchase Orders",
            "process_area": "Procure to Pay",
            "objective": "Verify PO creation and validation",
        },
        {
            "id": "22222222-2222-2222-2222-222222222222",
            "test_script_number": "P2P-INV-0002",
            "script_name": "Create Supplier Invoice",
            "module": "AP",
            "process": "Manage Supplier Invoices",
            "process_area": "Procure to Pay",
            "objective": "Verify AP Invoice entry against PO",
        },
    ]

    with patch("app.repositories.test_script_repository.test_script_repository.list_all", return_value=mock_scripts):
        req = TestSuiteRequest(process_area="Procure to Pay")
        res = test_suite_service.generate_suite(req, session_id="test_sess")
        assert res["status"] == "success"
        assert res["total_scripts"] == 2
        assert len(res["execution_steps"]) == 2
        assert len(res["coverage_gaps"]) > 0
        assert "Procure to Pay" in res["suite_name"]


def test_risk_assessment_service():
    mock_scripts = [
        {
            "id": "11111111-1111-1111-1111-111111111111",
            "test_script_number": "P2P-PO-0001",
            "script_name": "Create Purchase Order",
            "module": "PO",
            "process_area": "Procure to Pay",
        }
    ]
    mock_metrics = {
        "11111111-1111-1111-1111-111111111111": {
            "total_runs": 10,
            "failed_runs": 4,
            "passed_runs": 6,
            "flakiness_rate": 0.40,
        }
    }

    with patch("app.repositories.test_script_repository.test_script_repository.list_all", return_value=mock_scripts), \
         patch("app.repositories.execution_repository.execution_repository.get_script_execution_metrics", return_value=mock_metrics):
        req = RiskAssessmentRequest(filter_query="P2P")
        res = risk_assessment_service.assess_risk(req, session_id="test_sess")
        assert res["status"] == "success"
        assert res["total_scripts_assessed"] == 1
        assert len(res["risk_items"]) == 1
        assert res["overall_health_score"] > 0


def test_recommend_locator_repairs_service():
    mock_script = {
        "id": "11111111-1111-1111-1111-111111111111",
        "script_name": "Supplier Invoice Entry",
    }
    with patch("app.repositories.test_script_repository.test_script_repository.get_by_id", return_value=mock_script):
        res = failure_analysis_service.recommend_locator_repairs(script_name="Supplier Invoice Entry")
        assert res["status"] == "success"
        assert len(res["locator_repairs"]) > 0
        assert res["total_broken_locators"] > 0


def test_audit_analytics_telemetry():
    with patch("app.repositories.audit_repository.audit_repository.get_telemetry_summary", return_value={"total_calls": 50, "avg_duration_ms": 120.0, "error_count": 1, "success_rate": 98.0, "tool_distribution": {"semantic_search_tests": 30}}), \
         patch("app.repositories.audit_repository.audit_repository.get_recent_logs", return_value=[]), \
         patch("app.services.indexing_service.indexing_service.get_status", return_value={"is_indexing": False, "processed_scripts": 10, "total_scripts": 10}):
        res = audit_analytics_service.get_dashboard_telemetry()
        assert res["status"] == "success"
        assert res["telemetry"]["success_rate"] == 98.0
        assert res["vector_index_health"]["collection_name"] is not None


def test_tool_registry_enterprise_execution():
    with patch("app.services.test_suite_service.test_suite_service.generate_suite", return_value={"status": "success", "tool": "generate_test_suite"}):
        res = tool_registry_service.execute_tool("generate_test_suite", {"process_area": "Procure to Pay"})
        assert res["status"] == "success"

    with patch("app.services.risk_assessment_service.risk_assessment_service.assess_risk", return_value={"status": "success", "tool": "assess_test_risk"}):
        res = tool_registry_service.execute_tool("assess_test_risk", {"filter_query": "AP"})
        assert res["status"] == "success"

    with patch("app.services.failure_analysis_service.failure_analysis_service.recommend_locator_repairs", return_value={"status": "success", "tool": "recommend_locator_fixes"}):
        res = tool_registry_service.execute_tool("recommend_locator_fixes", {"script_name": "TS-001"})
        assert res["status"] == "success"
