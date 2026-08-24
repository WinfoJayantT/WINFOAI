import logging
from typing import Dict, Any, List
from sqlalchemy import text
from app.repositories.db import get_session
from app.repositories.test_script_repository import test_script_repository

logger = logging.getLogger(__name__)

class DuplicateDetectionService:
    
    def detect_duplicates(self, module: str = "") -> Dict[str, Any]:
        """
        Finds exact duplicate test scripts by analyzing the semantic documents and steps.
        If a module is provided, limits the search to that module.
        """
        try:
            duplicates_found = []
            
            with get_session() as db:
                # To find exact duplicates, we group by the exact semantic document content
                # which encapsulates the script steps, locators, and purpose.
                sql = """
                    SELECT a.semantic_document, array_agg(DISTINCT a.test_script_id::text) as script_ids
                    FROM ai_semantic_documents a
                    JOIN test_scripts t ON a.test_script_id = t.test_script_id
                    JOIN modules m ON t.module_id = m.module_id
                """
                
                params = {}
                if module and module.lower() not in ["all", "none", ""]:
                    sql += " WHERE m.module_name ILIKE :module "
                    params["module"] = f"%{module}%"
                    
                sql += """
                    GROUP BY a.semantic_document
                    HAVING count(DISTINCT a.test_script_id) > 1
                """
                
                res = db.execute(text(sql), params).fetchall()
                
                for row in res:
                    script_ids = row[1]
                    # Fetch script details for these IDs
                    scripts = []
                    for sid in script_ids:
                        rec = test_script_repository.get_by_id(sid)
                        if rec:
                            scripts.append({
                                "id": sid,
                                "script_number": rec.get("test_script_number", ""),
                                "script_name": rec.get("script_name", ""),
                                "module": rec.get("module", "")
                            })
                    
                    if len(scripts) > 1:
                        duplicates_found.append({
                            "match_score": 100.0,
                            "reason": "Exact Semantic Document & Step Sequence Match",
                            "scripts": scripts
                        })
                        
            return {
                "status": "success",
                "tool": "detect_duplicates",
                "module_filtered": module or "All Modules",
                "duplicate_clusters": duplicates_found,
                "total_clusters": len(duplicates_found)
            }
                
        except Exception as e:
            logger.error(f"Error in duplicate detection: {e}")
            return {
                "status": "error",
                "tool": "detect_duplicates",
                "message": "Failed to detect duplicates.",
                "reasoning": str(e)
            }

duplicate_detection_service = DuplicateDetectionService()
