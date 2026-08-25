"""
Test Script Repository
======================

This module manages all direct PostgreSQL interactions for the core `test_scripts` table.
It handles fetching, fuzzy matching, and deep relational joins (Modules, Process Areas) 
to fully hydrate test script entities before they are used by the AI domain services.

Key Responsibilities:
  1. Entity Hydration: Joins `test_scripts` with `modules` and `process_areas` to provide
     a complete business context for the AI.
  2. Type Serialization: Safely casts PostgreSQL-specific types (UUID, Decimal, Date) into
     JSON-serializable primitives for the FastAPI layer.
  3. Fuzzy Resolution: Implements fallback ILIKE querying to gracefully handle user typos 
     when requesting a script by name or number.
"""

import logging
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import text

from app.repositories.db import engine

# ── logger initialization ───────────────────────────────────────────────
logger = logging.getLogger(__name__)


# ── serialization utilities ─────────────────────────────────────────────
def _serialize_row(row: dict) -> dict:
    """
    Helper to convert non-JSON-serializable database objects (UUID, datetime, Decimal) 
    to JSON-serializable types for standard FastAPI output.
    """
    serialized = {}
    for k, v in row.items():
        if isinstance(v, UUID):
            serialized[k] = str(v)
        elif isinstance(v, (datetime, date)):
            serialized[k] = v.isoformat()
        elif isinstance(v, Decimal):
            serialized[k] = float(v)
        else:
            serialized[k] = v
            
    # Alias standard ID mappings
    if "test_script_id" in serialized and "id" not in serialized:
        serialized["id"] = serialized["test_script_id"]
    if "script_name" in serialized and "name" not in serialized:
        serialized["name"] = serialized["script_name"]
        
    return serialized


def _match_process(script_data: dict, processes: list) -> str:
    """
    Attempts to map a raw script to a high-level Oracle Modern Best Practice (MBP) process.
    Falls back to basic keyword matching on the script ID if no formal mapping exists.
    """
    from app.services.process_mapping_service import process_mapping_service
    mbp = process_mapping_service.get_mapping_for_script(script_data)
    if mbp and mbp.get("l1_process"):
        return mbp["l1_process"]
    
    if script_data.get("process_area"):
        return script_data["process_area"]
        
    num = (script_data.get("test_script_number") or "").upper()
    if "P2P" in num or "PO" in num or "SUP" in num:
        return "Supplier Invoice to Payment"
    elif "O2C" in num or "AR" in num:
        return "Customer Invoice to Receipt"
    elif "GL" in num or "R2R" in num:
        return "Period Close To Financial Reports"

    return "General Enterprise Process"


# ── class definition ──────────────────────────────────────────────────
class TestScriptRepository:
    """
    Repository layer for querying the `test_scripts` table and its dimensional relationships.
    """

    def _get_processes(self, conn) -> list:
        """Helper to fetch the master list of all known processes."""
        try:
            res = conn.execute(text("SELECT process_code, process_name FROM processes"))
            return [dict(r) for r in res.mappings().all()]
        except Exception:
            return []

    # ── public repository methods ───────────────────────────────────────
    def get_taxonomies(self) -> dict:
        """
        Retrieves the distinct lists of Modules, Processes, and Process Areas.
        Used to populate UI dropdowns and guide LLM prompt parameters.
        
        Returns:
            dict: Lists of taxonomy strings.
        """
        try:
            with engine.connect() as conn:
                processes = conn.execute(text("SELECT process_name FROM processes")).scalars().all()
                modules = conn.execute(text("SELECT module_name FROM modules")).scalars().all()
                process_areas = conn.execute(text("SELECT process_area_name FROM process_areas")).scalars().all()
                return {
                    "processes": processes,
                    "modules": modules,
                    "process_areas": process_areas,
                }
        except Exception as exc:
            logger.error("Failed to fetch taxonomies: %s", exc)
            return {"processes": [], "modules": [], "process_areas": []}

    def list_all(self) -> list:
        """
        Fetches every non-deleted test script in the database, joined with Module and Process Area names.
        
        Returns:
            list: Fully serialized list of all script dictionaries.
        """
        try:
            with engine.connect() as conn:
                processes = self._get_processes(conn)
                query = """
                    SELECT s.*, 
                           m.module_name as module, 
                           pa.process_area_name as process_area 
                    FROM test_scripts s
                    LEFT JOIN modules m ON s.module_id::text = m.module_id::text
                    LEFT JOIN process_areas pa ON m.process_area_id::text = pa.process_area_id::text
                    WHERE s.is_deleted = false
                """
                result = conn.execute(text(query))
                rows = result.mappings().all()
                
                serialized = []
                for row in rows:
                    d = _serialize_row(dict(row))
                    d["process"] = _match_process(d, processes)
                    serialized.append(d)
                return serialized
        except Exception as exc:
            logger.error("Failed to list test scripts from DB: %s", exc)
            return []

    def get_by_id(self, script_id: str) -> dict:
        """
        Fetches a single test script by its exact ID, Qualified Name, or Script Number.
        Implements a fallback fuzzy token search if an exact match is not found.
        
        Args:
            script_id (str): The search token provided by the user.
            
        Returns:
            dict: The serialized script payload, or None if completely unmatched.
        """
        try:
            with engine.connect() as conn:
                processes = self._get_processes(conn)
                
                # 1. Attempt exact match
                query = """
                    SELECT s.*, 
                           m.module_name as module, 
                           pa.process_area_name as process_area 
                    FROM test_scripts s
                    LEFT JOIN modules m ON s.module_id::text = m.module_id::text
                    LEFT JOIN process_areas pa ON m.process_area_id::text = pa.process_area_id::text
                    WHERE s.test_script_id::text = :id OR s.test_script_number = :id OR s.qualified_name = :id OR s.script_name = :id
                """
                result = conn.execute(
                    text(query),
                    {"id": script_id},
                )
                row = result.mappings().first()
                
                # 2. Fallback to fuzzy keyword weighting if exact match fails
                if not row:
                    words = [w for w in script_id.split() if len(w) > 2]
                    if words:
                        conditions = " OR ".join([f"s.script_name ILIKE :w_{i} OR s.qualified_name ILIKE :w_{i}" for i in range(len(words))])
                        order_cases = " + ".join([f"(CASE WHEN s.script_name ILIKE :w_{i} THEN 1 ELSE 0 END) + (CASE WHEN s.qualified_name ILIKE :w_{i} THEN 1 ELSE 0 END)" for i in range(len(words))])
                        
                        fuzzy_query = f"""
                            SELECT s.*, 
                                   m.module_name as module, 
                                   pa.process_area_name as process_area 
                            FROM test_scripts s
                            LEFT JOIN modules m ON s.module_id::text = m.module_id::text
                            LEFT JOIN process_areas pa ON m.process_area_id::text = pa.process_area_id::text
                            WHERE {conditions}
                            ORDER BY ({order_cases}) DESC
                            LIMIT 1
                        """
                        params = {f"w_{i}": f"%{w}%" for i, w in enumerate(words)}
                        result = conn.execute(text(fuzzy_query), params)
                        row = result.mappings().first()

                if row:
                    d = _serialize_row(dict(row))
                    d["process"] = _match_process(d, processes)
                    return d
                    
                return None
        except Exception as exc:
            logger.error("Failed to get script by id %s: %s", script_id, exc)
            return None

    def get_by_ids(self, script_ids: list) -> dict:
        """
        Efficiently fetches a batch of test scripts by their UUIDs in a single SQL query.
        
        Args:
            script_ids (list): List of script ID strings.
            
        Returns:
            dict: Mapping of str(script_id) -> serialized script dict.
        """
        if not script_ids:
            return {}
        try:
            with engine.connect() as conn:
                processes = self._get_processes(conn)
                query = """
                    SELECT s.*, 
                           m.module_name as module, 
                           pa.process_area_name as process_area 
                    FROM test_scripts s
                    LEFT JOIN modules m ON s.module_id::text = m.module_id::text
                    LEFT JOIN process_areas pa ON m.process_area_id::text = pa.process_area_id::text
                    WHERE s.test_script_id::text = ANY(:ids) AND s.is_deleted = false
                """
                result = conn.execute(text(query), {"ids": [str(sid) for sid in script_ids]})
                rows = result.mappings().all()
                
                lookup = {}
                for row in rows:
                    d = _serialize_row(dict(row))
                    d["process"] = _match_process(d, processes)
                    lookup[str(d.get("test_script_id") or d.get("id"))] = d
                return lookup
        except Exception as exc:
            logger.error("Failed to batch get scripts: %s", exc)
            return {}

    def get_script_by_identifier(self, identifier: str) -> dict:
        """Alias for get_by_id."""
        return self.get_by_id(identifier)


# ── singleton export ──────────────────────────────────────────────────
test_script_repository = TestScriptRepository()
