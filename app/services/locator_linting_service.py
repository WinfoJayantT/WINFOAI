import logging
import re
from typing import Dict, Any, List
from sqlalchemy import text
from app.repositories.db import get_session

logger = logging.getLogger(__name__)

class LocatorLintingService:
    
    def lint_locators(self, module: str) -> Dict[str, Any]:
        """
        Scans test script steps in a module for brittle locator patterns and recommends fixes.
        """
        if not module:
            return {
                "status": "error",
                "tool": "lint_locators",
                "message": "A module must be specified for locator linting to avoid scanning the entire database.",
                "reasoning": "Missing module parameter."
            }
            
        try:
            fragile_steps = []
            
            with get_session() as db:
                sql = """
                    SELECT t.test_script_number, t.script_name, m.step_description, m.locator_code, m.action
                    FROM master_steps m
                    JOIN test_scripts t ON m.script_id = t.test_script_id
                    JOIN modules mod ON t.module_id = mod.module_id
                    WHERE mod.module_name ILIKE :module
                      AND m.locator_code IS NOT NULL
                      AND m.locator_code != ''
                      AND m.is_active = true
                    ORDER BY t.test_script_number
                """
                
                res = db.execute(text(sql), {"module": f"%{module}%"}).fetchall()
                
                for row in res:
                    script_number = row[0]
                    script_name = row[1]
                    step_desc = row[2]
                    locator = row[3]
                    action = row[4]
                    
                    issues = []
                    recommendation = ""
                    
                    # Heuristic 1: Absolute XPaths starting with /html or /body
                    if locator.startswith("/html") or locator.startswith("/body"):
                        issues.append("Absolute XPath")
                        recommendation = "Use relative semantic selectors (e.g., //button[@id='save'] or //input[@name='username']) instead of absolute DOM paths which break easily on UI changes."
                    
                    # Heuristic 2: Deep nesting with indices
                    elif re.search(r'\[\d+\]/.*\[\d+\]', locator):
                        issues.append("Deeply Nested Positional Index")
                        recommendation = "Avoid relying on multiple positional indices (e.g., tr[3]/td[4]). Try anchoring by text or nearby labels using preceding/following axes."
                    
                    # Heuristic 3: Auto-generated ugly IDs (e.g., id='ext-gen1045')
                    elif re.search(r'@id=[\'"]ext-gen\d+[\'"]', locator):
                        issues.append("Dynamic Framework ID")
                        recommendation = "ExtJS or dynamic IDs like 'ext-gen*' change on every refresh. Use other attributes like name, title, or label."
                    
                    if issues:
                        fragile_steps.append({
                            "script_number": script_number,
                            "script_name": script_name,
                            "step_description": step_desc,
                            "action": action,
                            "locator": locator,
                            "issues": issues,
                            "recommendation": recommendation
                        })
                        
                        # Limit to top 20 to avoid massive payloads
                        if len(fragile_steps) >= 20:
                            break
                            
            return {
                "status": "success",
                "tool": "lint_locators",
                "module_scanned": module,
                "total_fragile_locators_found": len(fragile_steps),
                "fragile_steps": fragile_steps
            }
            
        except Exception as e:
            logger.error(f"Error in locator linting: {e}")
            return {
                "status": "error",
                "tool": "lint_locators",
                "message": "Failed to lint locators.",
                "reasoning": str(e)
            }

locator_linting_service = LocatorLintingService()
