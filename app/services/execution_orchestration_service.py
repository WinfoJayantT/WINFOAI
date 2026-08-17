from typing import Any, Dict, List

from app.clients.winfotest_execution_client import winfotest_execution_client


class ExecutionOrchestrationService:
    """Section 7 / 17. Deliberately thin — validation/permission checks belong
    in tool_registry_service before this is ever called; this just forwards
    to the (currently stubbed) WinfoTest execution client."""

    def run(self, test_script_ids: List[str]) -> Dict[str, Any]:
        return winfotest_execution_client.run_test_group(test_script_ids)

    def execute_previous_result(self, session_id: str) -> Dict[str, Any]:
        from app.services.conversation_state_service import conversation_state_service
        state = conversation_state_service.get(session_id)
        if state.can_execute_previous_result and state.last_result_script_ids:
            return winfotest_execution_client.run_test_group(state.last_result_script_ids)
        
        return {
            "status": "insufficient_data",
            "message": "No previous test results are available to execute.",
        }


execution_orchestration_service = ExecutionOrchestrationService()
