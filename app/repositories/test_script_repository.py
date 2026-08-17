# STREAMING_CHUNK:Initializing test script repository with UUID serialization handling...
import logging
logger = logging.getLogger(__name__)
from uuid import UUID
from sqlalchemy import text
from app.core.config import settings
from app.repositories.db import engine


import re

from datetime import datetime, date
from decimal import Decimal

def _serialize_row(row: dict) -> dict:
    """Helper to convert non-JSON-serializable objects (UUID, datetime, Decimal) to JSON-serializable types."""
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
    if "test_script_id" in serialized and "id" not in serialized:
        serialized["id"] = serialized["test_script_id"]
    if "script_name" in serialized and "name" not in serialized:
        serialized["name"] = serialized["script_name"]
    return serialized


def _match_process(script_data: dict, processes: list) -> str:
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


class TestScriptRepository:
    def _get_processes(self, conn) -> list:
        try:
            res = conn.execute(text("SELECT process_code, process_name FROM processes"))
            return [dict(r) for r in res.mappings().all()]
        except Exception:
            return []

    def get_taxonomies(self) -> dict:
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

    def list_all(self):
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

    def get_by_id(self, script_id: str):
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
                    WHERE s.test_script_id::text = :id OR s.test_script_number = :id OR s.qualified_name = :id OR s.script_name = :id
                """
                result = conn.execute(
                    text(query),
                    {"id": script_id},
                )
                row = result.mappings().first()
                
                # Fallback to fuzzy word match if exact match fails
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

    def get_script_by_identifier(self, identifier: str):
        return self.get_by_id(identifier)




test_script_repository = TestScriptRepository()
