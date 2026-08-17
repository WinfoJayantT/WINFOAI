import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select

from app.models.orm import TestRunScript, TestRunScriptStep, TestRunScriptStepResult
from app.repositories.db import get_session

logger = logging.getLogger(__name__)


class ExecutionRepository:
    """Read access to execution result tables for failure analysis (section 12.4)."""

    def get_latest_failure(self, test_script_id: str) -> Optional[Dict[str, Any]]:
        try:
            with get_session() as db:
                run_script_stmt = (
                    select(TestRunScript)
                    .where(TestRunScript.test_script_id == UUID(test_script_id))
                    .order_by(TestRunScript.started_at.desc())
                )
                run_script = db.execute(run_script_stmt).scalars().first()
                if run_script is None:
                    return None

                step_stmt = (
                    select(TestRunScriptStep, TestRunScriptStepResult)
                    .join(
                        TestRunScriptStepResult,
                        TestRunScriptStepResult.test_run_script_step_id == TestRunScriptStep.id,
                    )
                    .where(TestRunScriptStep.test_run_script_id == run_script.id)
                    .where(TestRunScriptStepResult.status == "FAILED")
                    .order_by(TestRunScriptStepResult.executed_at.desc())
                )
                row = db.execute(step_stmt).first()
                if row is None:
                    return None
                step, result = row
                return {
                    "step_no": step.step_no,
                    "step_action": step.step_action,
                    "step_description": step.step_description,
                    "error_message": result.error_message,
                    "dom_snapshot": result.dom_snapshot,
                    "executed_at": result.executed_at.isoformat() if result.executed_at else None,
                }
        except Exception as exc:
            logger.warning(f"Error fetching latest failure for script {test_script_id}: {exc}")
            return None

    def get_step_dom_and_locators(self, test_script_id: str) -> List[Dict[str, Any]]:
        try:
            with get_session() as db:
                try:
                    script_uuid = UUID(test_script_id) if isinstance(test_script_id, str) else test_script_id
                except Exception:
                    return []
                    
                run_script_stmt = (
                    select(TestRunScript)
                    .where(TestRunScript.test_script_id == script_uuid)
                    .order_by(TestRunScript.started_at.desc())
                )
                run_scripts = db.execute(run_script_stmt).scalars().all()
                if not run_scripts:
                    return []

                latest_run = run_scripts[0]
                step_stmt = (
                    select(TestRunScriptStep, TestRunScriptStepResult)
                    .join(
                        TestRunScriptStepResult,
                        TestRunScriptStepResult.test_run_script_step_id == TestRunScriptStep.id,
                    )
                    .where(TestRunScriptStep.test_run_script_id == latest_run.id)
                    .order_by(TestRunScriptStep.step_no.asc())
                )
                rows = db.execute(step_stmt).all()
                results = []
                for step, result in rows:
                    results.append({
                        "step_no": step.step_no,
                        "step_action": step.step_action or "click",
                        "step_description": step.step_description or "",
                        "input_parameter": step.input_parameter or "",
                        "locator_code": step.locator_code or "",
                        "fallback_locator_code": step.fallback_locator_code or "",
                        "status": result.status if result else "UNKNOWN",
                        "error_message": result.error_message if result else None,
                        "dom_snapshot": result.dom_snapshot if result else None,
                    })
                return results
        except Exception as exc:
            logger.warning(f"Error fetching step locators for script {test_script_id}: {exc}")
            return []

    def get_script_execution_metrics(self) -> Dict[str, Dict[str, Any]]:
        try:
            with get_session() as db:
                stmt = select(TestRunScript)
                run_scripts = db.execute(stmt).scalars().all()
                
                metrics: Dict[str, Dict[str, Any]] = {}
                for rs in run_scripts:
                    s_id = str(rs.test_script_id)
                    if s_id not in metrics:
                        metrics[s_id] = {
                            "total_runs": 0,
                            "failed_runs": 0,
                            "passed_runs": 0,
                            "last_status": rs.status,
                        }
                    metrics[s_id]["total_runs"] += 1
                    if rs.status == "FAILED":
                        metrics[s_id]["failed_runs"] += 1
                    elif rs.status in ("PASSED", "SUCCESS"):
                        metrics[s_id]["passed_runs"] += 1
                    metrics[s_id]["last_status"] = rs.status

                for s_id, m in metrics.items():
                    total = m["total_runs"]
                    m["flakiness_rate"] = round(m["failed_runs"] / total, 2) if total > 0 else 0.0

                return metrics
        except Exception as exc:
            logger.warning(f"Error calculating execution metrics: {exc}")
            return {}


execution_repository = ExecutionRepository()
