"""
Test Step Repository
====================

This module manages retrieval of the granular, ordered UI actions (steps) that make up a test script.

Key Responsibilities:
  1. Cascade Retrieval: Attempts to load canonical steps from `master_steps`. If none exist,
     it falls back to loading steps from the most recently executed `test_run_scripts`.
  2. Step Deduplication: Ensures that identical steps (by step number and description) are
     not accidentally duplicated when parsing legacy DB schemas.
"""

import logging
from typing import Any

from sqlalchemy import text

from app.repositories.db import engine

# ── logger initialization ───────────────────────────────────────────────
logger = logging.getLogger(__name__)


# ── class definition ──────────────────────────────────────────────────
class StepRepository:
    """
    Data Access Object (DAO) for interacting with granular test step records.
    """

    # ── public repository methods ───────────────────────────────────────
    def get_ordered_steps(self, script_id: str) -> list[dict[str, Any]]:
        """
        Retrieves ordered steps directly from `master_steps` or `test_run_script_steps`.
        
        Args:
            script_id (str): The primary key ID of the parent test script.
            
        Returns:
            List[Dict]: An ordered list of dictionaries representing individual test steps.
        """
        try:
            with engine.connect() as conn:
                import uuid as _uuid
                # If script_id looks like a UUID, use it directly
                # Only do a get_by_id lookup if it looks like a script number / name (not UUID)
                resolved_id = str(script_id)
                try:
                    _uuid.UUID(resolved_id)  # Will raise ValueError if not a valid UUID
                except (ValueError, AttributeError):
                    # Not a UUID, resolve via repository
                    from app.repositories.test_script_repository import (
                        test_script_repository,
                    )
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
                    
                    return []
                    
        except Exception as exc:
            logger.error("Querying steps failed for script_id %s: %s", script_id, exc)
            return []

    def get_ordered_steps_for_scripts(self, script_ids: list[str]) -> dict[str, list[dict[str, Any]]]:
        """
        Retrieves ordered steps for an entire batch of script IDs in a single SQL query.
        
        Args:
            script_ids (List[str]): List of script ID strings.
            
        Returns:
            Dict[str, List[Dict]]: Mapping of script_id -> ordered list of step dicts.
        """
        if not script_ids:
            return {}
            
        id_strs = [str(sid) for sid in script_ids]
        steps_by_script: dict[str, list[dict[str, Any]]] = {sid: [] for sid in id_strs}
        
        try:
            with engine.connect() as conn:
                # 1. Master steps batch query
                try:
                    master_query = """
                        SELECT id, script_id, step_no, action as step_action, action, step_description, input_parameter 
                        FROM master_steps 
                        WHERE script_id::text = ANY(:ids)
                        ORDER BY script_id, step_no ASC
                    """
                    result = conn.execute(text(master_query), {"ids": id_strs})
                    rows = result.mappings().all()
                    
                    seen_by_script: dict[str, set] = {sid: set() for sid in id_strs}
                    for r in rows:
                        d = dict(r)
                        sid = str(d.get("script_id"))
                        key = (d.get("step_no"), d.get("action"), d.get("step_description"))
                        if sid in steps_by_script and key not in seen_by_script.setdefault(sid, set()):
                            seen_by_script[sid].add(key)
                            steps_by_script[sid].append(d)
                except Exception as e:
                    logger.debug("Batch master_steps lookup failed: %s", e)

                # 2. Check which scripts didn't find master_steps and fallback to test_run_script_steps
                missing_sids = [sid for sid in id_strs if not steps_by_script[sid]]
                if missing_sids:
                    try:
                        fallback_query = """
                            SELECT DISTINCT ON (trs.source_test_script_id, s.step_no)
                                   s.test_run_script_step_id as id,
                                   trs.source_test_script_id as script_id,
                                   s.step_no,
                                   s.action as step_action,
                                   s.action,
                                   s.step_description,
                                   s.input_parameter
                            FROM test_run_script_steps s
                            JOIN test_run_scripts trs ON s.test_run_script_id = trs.test_run_script_id
                            WHERE trs.source_test_script_id::text = ANY(:ids)
                            ORDER BY trs.source_test_script_id, s.step_no ASC, trs.creation_date DESC NULLS LAST
                        """
                        result = conn.execute(text(fallback_query), {"ids": missing_sids})
                        rows = result.mappings().all()
                        for r in rows:
                            d = dict(r)
                            sid = str(d.get("script_id"))
                            if sid in steps_by_script:
                                steps_by_script[sid].append(d)
                    except Exception as e:
                        logger.debug("Batch test_run_script_steps fallback failed: %s", e)
                        
            return steps_by_script
        except Exception as exc:
            logger.error("Failed to batch get ordered steps: %s", exc)
            return steps_by_script

    def update_locator(self, script_id: str, step_no: int, new_locator: str) -> bool:
        """
        Instantly patches the database with a self-healed resilient locator for a specific step.
        """
        try:
            with engine.connect() as conn:
                import uuid as _uuid
                resolved_id = str(script_id)
                try:
                    _uuid.UUID(resolved_id)
                except (ValueError, AttributeError):
                    from app.repositories.test_script_repository import (
                        test_script_repository,
                    )
                    script = test_script_repository.get_by_id(script_id)
                    if script:
                        resolved_id = str(script.get("test_script_id") or script.get("id") or script_id)
                
                query = """
                    UPDATE master_steps 
                    SET locator_code = :new_locator, updated_at = NOW() 
                    WHERE script_id::text = :script_id AND step_no = :step_no
                """
                result = conn.execute(text(query), {
                    "new_locator": new_locator,
                    "script_id": resolved_id,
                    "step_no": step_no
                })
                conn.commit()
                return result.rowcount > 0
        except Exception as exc:
            logger.error("Failed to heal locator for script_id %s step %s: %s", script_id, step_no, exc)
            return False

# ── singleton export ──────────────────────────────────────────────────
step_repository = StepRepository()
