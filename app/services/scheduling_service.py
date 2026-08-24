import logging
from typing import Dict, Any
from datetime import datetime, timezone
import uuid
import time

from sqlalchemy import select

from app.repositories.db import get_session
from app.winfo_test_orm.models.test_runs import TestRuns
from app.winfo_test_orm.models.workspace import Workspace
from app.winfo_test_orm.models.workspace_configurations import WorkspaceConfiguration
from app.repositories.test_script_repository import test_script_repository
from app.services.debug_trace_service import debug_trace_service

logger = logging.getLogger(__name__)

class SchedulingService:
    def schedule_run(self, target_suite: str, scheduled_time: str) -> Dict[str, Any]:
        """
        Schedules a test run.
        :param target_suite: The name of the suite or script to run.
        :param scheduled_time: ISO-8601 formatted datetime string.
        """
        start_time = time.time()
        logger.info(f"Scheduling test run for '{target_suite}' at '{scheduled_time}'")

        # 1. Parse time (expects ISO-8601 from LLM)
        try:
            # Replace Z with +00:00 to support standard python fromisoformat
            time_str = scheduled_time.replace("Z", "+00:00")
            parsed_time = datetime.fromisoformat(time_str)
            if parsed_time.tzinfo is None:
                parsed_time = parsed_time.replace(tzinfo=timezone.utc)
        except Exception as e:
            logger.error(f"Failed to parse time {scheduled_time}: {e}")
            parsed_time = datetime.now(timezone.utc)
        
        # 2. Find target script/suite
        script = test_script_repository.get_by_id(target_suite)
        
        if not script:
            return {
                "status": "not_found",
                "tool": "schedule_test_run",
                "target_name": target_suite,
                "scheduled_time": parsed_time.isoformat(),
                "message": f"Could not find any script or suite matching '{target_suite}'."
            }

        # 3. Get workspace context
        try:
            with get_session() as db:
                ws = db.execute(select(Workspace)).scalars().first()
                ws_conf = db.execute(select(WorkspaceConfiguration)).scalars().first()
                
                ws_id = ws.workspace_id if ws else uuid.uuid4()
                conf_id = ws_conf.workspace_configurations_id if ws_conf else uuid.uuid4()
                created_by = uuid.uuid4()

                # 4. Insert TestRun
                new_run = TestRuns(
                    workspace_id=ws_id,
                    configuration_id=conf_id,
                    run_type="RUN",
                    run_name=f"Scheduled Run: {script.get('name')}",
                    run_description=f"Auto-scheduled by AI. Target: {script.get('name')}",
                    run_status_code="SCHEDULED",
                    scheduled_start_time=parsed_time,
                    scheduled_time_utc=parsed_time,
                    created_by=created_by,
                    creation_date=datetime.now(timezone.utc)
                )
                db.add(new_run)
                db.commit()
                db.refresh(new_run)
                new_run_id = str(new_run.test_run_id)
        except Exception as e:
            logger.error(f"Failed to insert scheduled run: {e}")
            return {
                "status": "error",
                "tool": "schedule_test_run",
                "message": f"Database error while scheduling: {e}"
            }

        trace = debug_trace_service.build_trace(
            intent="schedule_test_run",
            tool_name="schedule_test_run",
            parsed_args={"target_suite": target_suite, "scheduled_time": scheduled_time},
            repo_path="scheduling_service.schedule_run -> Insert wt.test_runs",
            execution_time_ms=int((time.time() - start_time) * 1000),
        )

        return {
            "status": "success",
            "tool": "schedule_test_run",
            "run_id": new_run_id,
            "script_name": script.get("name"),
            "script_number": script.get("test_script_number"),
            "scheduled_time": parsed_time.isoformat(),
            "debug_trace": trace
        }

scheduling_service = SchedulingService()
