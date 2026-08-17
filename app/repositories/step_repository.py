# STREAMING_CHUNK:Initializing direct test_run_script_steps repository...
import logging
from typing import Any, Dict, List
from sqlalchemy import text
from app.core.config import settings
from app.repositories.db import engine

logger = logging.getLogger(__name__)


class StepRepository:
    def get_ordered_steps(self, script_id: str) -> List[Dict[str, Any]]:
        """Retrieves ordered steps directly from master_steps or test_run_script_steps."""
        try:
            with engine.connect() as conn:
                resolved_id = str(script_id)
                from app.repositories.test_script_repository import test_script_repository
                script = test_script_repository.get_by_id(script_id)
                if script:
                    resolved_id = str(script.get("test_script_id") or script.get("id") or script_id)

                # 1. Try master_steps first (directly linked via script_id)
                try:
                    master_query = """
                        SELECT id, script_id, step_no, action as step_action, action, step_description, input_parameter 
                        FROM master_steps 
                        WHERE script_id::text = :script_id
                        ORDER BY step_no ASC
                    """
                    result = conn.execute(text(master_query), {"script_id": resolved_id})
                    rows = result.mappings().all()
                    if rows:
                        seen = set()
                        unique_steps = []
                        for r in rows:
                            d = dict(r)
                            key = (d.get("step_no"), d.get("action"), d.get("step_description"))
                            if key not in seen:
                                seen.add(key)
                                unique_steps.append(d)
                        return unique_steps
                except Exception as e:
                    logger.debug("master_steps lookup not available or failed: %s", e)

                # 2. Fallback to test_run_script_steps (take ONLY the latest single test run)
                try:
                    run_query = """
                        SELECT s.test_run_script_step_id as id, s.test_run_script_id, s.step_no, s.action as step_action, s.action, s.step_description, s.input_parameter 
                        FROM test_run_script_steps s
                        WHERE s.test_run_script_id = (
                            SELECT test_run_script_id FROM test_run_scripts 
                            WHERE source_test_script_id::text = :script_id 
                            ORDER BY creation_date DESC NULLS LAST LIMIT 1
                        )
                        ORDER BY s.step_no ASC
                    """
                    result = conn.execute(text(run_query), {"script_id": resolved_id})
                    rows = result.mappings().all()
                    seen = set()
                    unique_steps = []
                    for r in rows:
                        d = dict(r)
                        key = (d.get("step_no"), d.get("action"), d.get("step_description"))
                        if key not in seen:
                            seen.add(key)
                            unique_steps.append(d)
                    return unique_steps
                except Exception as e:
                    logger.debug("test_run_script_steps lookup failed: %s", e)
                    return []
        except Exception as exc:
            logger.error("Querying steps failed for script_id %s: %s", script_id, exc)
            return []


step_repository = StepRepository()
