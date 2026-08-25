import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select

from app.repositories.db import get_session
from app.winfo_test_orm.models.modules import Modules
from app.winfo_test_orm.models.test_run_scripts import TestRunScripts
from app.winfo_test_orm.models.test_scripts import TestScripts

logger = logging.getLogger(__name__)

class AnalyticsService:
    
    def _parse_timeframe(self, timeframe: str) -> datetime:
        """Helper to parse fuzzy natural language timeframe into a concrete datetime threshold."""
        now = datetime.now(timezone.utc)
        timeframe = timeframe.lower().strip() if timeframe else ""
        
        if "yesterday" in timeframe:
            return now - timedelta(days=2)
        elif "week" in timeframe:
            return now - timedelta(days=7)
        elif "month" in timeframe:
            return now - timedelta(days=30)
        elif "today" in timeframe:
            # Beginning of today
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            # Default to last 30 days if unclear
            return now - timedelta(days=30)

    def analyze_results(self, timeframe: str = "", module: str = "", status: str = "") -> dict[str, Any]:
        """
        Analyzes test run execution results based on natural language extracted filters.
        """
        threshold_date = self._parse_timeframe(timeframe)
        
        try:
            with get_session() as db:
                query = select(TestRunScripts).where(TestRunScripts.creation_date >= threshold_date)
                
                # Optional module filtering
                if module and module.lower() != "all" and module.lower() != "none":
                    query = query.join(TestScripts, TestRunScripts.source_test_script_id == TestScripts.test_script_id)
                    query = query.join(Modules, TestScripts.module_id == Modules.module_id)
                    query = query.where(Modules.module_name.ilike(f"%{module}%"))

                # Execute query and compute aggregations
                all_scripts = db.execute(query).scalars().all()
                
                total = len(all_scripts)
                passed = sum(1 for s in all_scripts if s.execution_status_code == 'PASSED')
                failed = sum(1 for s in all_scripts if s.execution_status_code == 'FAILED')
                
                pass_rate = (passed / total * 100) if total > 0 else 0.0
                
                # Get top 5 recent failures
                failed_scripts = [s for s in all_scripts if s.execution_status_code == 'FAILED']
                # Sort by creation_date descending
                failed_scripts.sort(key=lambda x: x.creation_date or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
                top_failures = failed_scripts[:5]
                
                recent_failures_formatted = []
                for fs in top_failures:
                    recent_failures_formatted.append({
                        "script_number": fs.test_script_code,
                        "script_name": fs.test_script_name,
                        "error_message": fs.error_message or "Unknown Error",
                        "execution_time": fs.creation_date.isoformat() if fs.creation_date else "N/A"
                    })

                return {
                    "status": "success",
                    "tool": "analyze_test_results",
                    "metrics": {
                        "total_executed": total,
                        "passed": passed,
                        "failed": failed,
                        "pass_rate_percentage": round(pass_rate, 1),
                        "timeframe_parsed": threshold_date.isoformat(),
                        "module_filtered": module or "All Modules"
                    },
                    "recent_failures": recent_failures_formatted
                }
                
        except Exception as e:
            logger.error(f"Error in analyze_results: {e}")
            return {
                "status": "error",
                "tool": "analyze_test_results",
                "message": "Failed to analyze test results.",
                "reasoning": str(e)
            }

analytics_service = AnalyticsService()
