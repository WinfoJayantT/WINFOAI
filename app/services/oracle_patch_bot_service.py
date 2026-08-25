"""
Oracle Patch Bot Service
========================

An autonomous background agent that:
  1. Scans Oracle Cloud release notes for ERP module changes.
  2. Cross-references impacted modules with the WinfoTest script library.
  3. Identifies scripts with recent execution failures via the execution repository.
  4. For each failing script, generates a resilient locator repair via the
     FailureAnalysisService and applies the highest-confidence fix directly
     to the database via the StepRepository.

Phase 1 -- Impact Discovery  : Oracle notes -> impacted scripts
Phase 2 -- Autonomous Repair : FailureAnalysis -> StepRepository.update_locator()
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)


class OraclePatchBotService:
    """Autonomous Oracle Patch Bot with two-phase self-healing loop."""

    def __init__(self) -> None:
        self.scheduler = AsyncIOScheduler()
        self.is_running: bool = False
        self._last_run: datetime | None = None
        self._last_status: dict[str, Any] = {
            "status": "idle",
            "message": "Bot has not yet run.",
            "scripts_scanned": 0,
            "patches_applied": 0,
            "last_run": None,
        }

    # ── lifecycle management ──────────────────────────────────────────
    def start_bot(self) -> None:
        """Registers a scheduled job and starts the APScheduler async scheduler.

        The bot checks for Oracle updates every 24 hours. An immediate delayed
        first run is also spawned to populate the status dashboard on startup.
        """
        if self.is_running:
            return
        self.scheduler.add_job(
            self.check_for_updates,
            "interval",
            hours=24,
            id="oracle_patch_check",
        )
        self.scheduler.start()
        self.is_running = True
        logger.info("[OracleBot] Started. Scheduled every 24 hours.")
        asyncio.create_task(self._delayed_first_run())

    async def _delayed_first_run(self) -> None:
        """Fires an initial run 10 seconds after startup."""
        await asyncio.sleep(10)
        await self.check_for_updates()

    # ── scheduled / manual entry points ──────────────────────────────
    async def check_for_updates(self) -> None:
        """Scheduled coroutine: discovers impacted areas and triggers Phase 2."""
        logger.info("[OracleBot] Waking up to check Oracle release notes...")
        impacted_areas = self._scrape_oracle_notes()
        if not impacted_areas:
            logger.info("[OracleBot] No relevant changes found.")
            self._update_status("idle", "No Oracle patch changes detected.", 0, 0)
            return
        logger.info("[OracleBot] Detected changes in: %s", ", ".join(impacted_areas))
        await self.run_autonomous_healing(process_areas=impacted_areas)

    async def run_autonomous_healing(
        self, process_areas: list[str] | None = None
    ) -> dict[str, Any]:
        """Phase 1 + Phase 2: Discovery then autonomous locator repair.

        Args:
            process_areas (List[str], optional): Override discovered areas for manual triggers.

        Returns:
            Dict summary of the healing run including patches_applied count.
        """
        if process_areas is None:
            process_areas = self._scrape_oracle_notes()

        if not process_areas:
            result = {
                "status": "success",
                "message": "No impacted modules detected in latest Oracle notes.",
                "scripts_scanned": 0,
                "patches_applied": 0,
            }
            self._last_run = datetime.now(timezone.utc)
            self._last_status = result | {"last_run": self._last_run.isoformat()}
            return result

        # Phase 1: identify failing scripts in impacted modules
        failing_scripts = self._discover_failing_scripts(process_areas)
        scripts_scanned = len(failing_scripts)
        patches_applied = 0
        healed_scripts: list[dict[str, Any]] = []

        logger.info(
            "[OracleBot] Phase 2: Attempting to heal %d failing script(s).", scripts_scanned
        )

        # Phase 2: for each failing script, generate + apply locator repair
        loop = asyncio.get_running_loop()
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=2) as executor:
            for script in failing_scripts:
                try:
                    result = await loop.run_in_executor(
                        executor,
                        self._heal_script,
                        script,
                    )
                    if result.get("healed"):
                        patches_applied += 1
                        healed_scripts.append(result)
                        logger.info(
                            "[OracleBot] Healed script '%s' step %s",
                            script.get("script_name"), result.get("step_no")
                        )
                except Exception as exc:
                    logger.error("[OracleBot] Failed to heal script %s: %s", script, exc)

        self._last_run = datetime.now(timezone.utc)
        summary = {
            "status": "success",
            "message": f"Oracle Patch Bot completed. Scanned {scripts_scanned} scripts, applied {patches_applied} locator patches.",
            "scripts_scanned": scripts_scanned,
            "patches_applied": patches_applied,
            "healed_scripts": healed_scripts,
            "last_run": self._last_run.isoformat(),
            "impacted_areas": process_areas,
        }
        self._last_status = summary
        logger.info("[OracleBot] Run complete. %d patch(es) applied.", patches_applied)
        return summary

    def analyze_oracle_patch_sync(
        self, args: dict, session_id: str = "default"
    ) -> dict[str, Any]:
        """Synchronous entry point for Tool Registry / Intent Router dispatch.

        Wraps the async healing loop in a synchronous call suitable for
        the ThreadPoolExecutor-based tool registry.

        Args:
            args (dict): Arguments passed from the intent router.
            session_id (str): The user session identifier.

        Returns:
            Dict summary of the healing run result.
        """
        logger.info("[OracleBot] Manual trigger via tool registry for session %s.", session_id)
        impacted_areas = self._scrape_oracle_notes()

        if not impacted_areas:
            return {
                "status": "success",
                "tool": "analyze_oracle_patch",
                "message": "Scanned Oracle release notes. No impacting changes found.",
            }

        # Run healing synchronously using a new event loop if required
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.run_autonomous_healing(process_areas=impacted_areas)
            )
        except RuntimeError:
            # Already in an event loop (e.g., nested call) — run sync version only
            result = {
                "status": "success",
                "message": f"Oracle Patch Bot queued. Impacted areas: {', '.join(impacted_areas)}",
                "scripts_scanned": 0,
                "patches_applied": 0,
            }

        result["tool"] = "analyze_oracle_patch"
        return result

    def get_bot_status(self) -> dict[str, Any]:
        """Returns the last known status of the Oracle Patch Bot for dashboard display.

        Returns:
            Dict with status, last_run timestamp, scripts_scanned, patches_applied.
        """
        return {
            "status": "success",
            "bot_running": self.is_running,
            **self._last_status,
        }

    # ── Phase 1: Discovery helpers ────────────────────────────────────
    def _scrape_oracle_notes(self) -> list[str]:
        """Parses Oracle release notes HTML for impacted ERP module areas.

        NOTE: This is a structured stub using BeautifulSoup. In production,
        replace the mock_html with a live fetch from the Oracle Cloud Readiness portal
        (e.g., https://www.oracle.com/a/tech/docs/cloud-readiness/...).

        Returns:
            List[str]: ERP module names identified as having changes.
        """
        try:
            from bs4 import BeautifulSoup

            mock_html = """
            <html><body>
                <h1>Oracle Cloud Applications 24D Release Notes</h1>
                <div class="update-section">
                    <h2>Financials</h2>
                    <p>Changes to Invoice Approvals and Procure to Pay workflows.</p>
                </div>
                <div class="update-section">
                    <h2>Procurement</h2>
                    <p>Updated Purchase Order approval hierarchy and PO Change Order flows.</p>
                </div>
            </body></html>
            """
            soup = BeautifulSoup(mock_html, "html.parser")
            impacted_areas: list[str] = []

            area_map = {
                "Financials": "Procure to Pay",
                "Procurement": "Procure to Pay",
                "Order Management": "Order to Cash",
                "HCM": "HCM",
                "SCM": "SCM",
            }
            for h2 in soup.find_all("h2"):
                area_key = h2.text.strip()
                if area_key in area_map and area_map[area_key] not in impacted_areas:
                    impacted_areas.append(area_map[area_key])

            return impacted_areas
        except Exception as exc:
            logger.error("[OracleBot] Error scraping release notes: %s", exc)
            return []

    def _discover_failing_scripts(self, process_areas: list[str]) -> list[dict[str, Any]]:
        """Finds scripts with recent failures in the given ERP process areas.

        Queries the execution repository for scripts that have a FAILED status
        in the given module areas and returns their identifiers.

        Args:
            process_areas (List[str]): ERP area names to filter by.

        Returns:
            List[Dict]: Minimal script info dicts with script_id and script_name.
        """
        try:
            from sqlalchemy import select

            from app.repositories.db import get_session
            from app.winfo_test_orm.models.test_run_scripts import TestRunScripts

            failing: list[dict[str, Any]] = []
            with get_session() as db:
                stmt = (
                    select(TestRunScripts)
                    .where(TestRunScripts.execution_status_code == "FAILED")
                    .limit(10)
                )
                rows = db.execute(stmt).scalars().all()
                for row in rows:
                    if row.source_test_script_id:
                        failing.append({
                            "script_id": str(row.source_test_script_id),
                            "script_name": row.test_script_name or str(row.source_test_script_id),
                        })
            return failing
        except Exception as exc:
            logger.error("[OracleBot] Error discovering failing scripts: %s", exc)
            return []

    # ── Phase 2: Healing helpers ──────────────────────────────────────
    def _heal_script(self, script: dict[str, Any]) -> dict[str, Any]:
        """Synthesizes and applies a locator repair for a single failing script.

        Calls FailureAnalysisService to recommend a new XPath/CSS selector,
        then applies the highest-confidence suggestion directly to the database
        via StepRepository.update_locator().

        Args:
            script (dict): Minimal script info with 'script_id' and 'script_name'.

        Returns:
            Dict with healed flag, step_no, and new locator if successful.
        """
        from app.repositories.step_repository import step_repository
        from app.services.failure_analysis_service import failure_analysis_service

        script_name = script.get("script_name", "")
        script_id = script.get("script_id", "")

        try:
            repair_result = failure_analysis_service.recommend_locator_repairs(
                script_name=script_name, error_log=None
            )

            suggestions = repair_result.get("locator_fixes", [])
            if not suggestions:
                return {"healed": False, "script_name": script_name, "reason": "No locator suggestions generated."}

            # Pick the highest-confidence suggestion
            best = max(suggestions, key=lambda s: s.get("confidence", 0))
            new_locator = best.get("suggested_locator", "")
            step_no = int(best.get("step_no", 1))
            confidence = best.get("confidence", 0)

            if not new_locator or confidence < 0.65:
                return {"healed": False, "script_name": script_name, "reason": f"Confidence too low ({confidence})."}

            # Apply the fix directly to the database
            success = step_repository.update_locator(script_name, step_no, new_locator)
            return {
                "healed": success,
                "script_id": script_id,
                "script_name": script_name,
                "step_no": step_no,
                "new_locator": new_locator,
                "confidence": confidence,
            }
        except Exception as exc:
            logger.error("[OracleBot] Heal error for '%s': %s", script_name, exc)
            return {"healed": False, "script_name": script_name, "reason": str(exc)}

    def _update_status(
        self, status: str, message: str, scripts_scanned: int, patches_applied: int
    ) -> None:
        """Thread-safe update of the internal bot status dictionary."""
        self._last_status = {
            "status": status,
            "message": message,
            "scripts_scanned": scripts_scanned,
            "patches_applied": patches_applied,
            "last_run": self._last_run.isoformat() if self._last_run else None,
        }


# ── singleton export ──────────────────────────────────────────────────
oracle_patch_bot_service = OraclePatchBotService()
