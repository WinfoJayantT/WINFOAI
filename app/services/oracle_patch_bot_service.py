import asyncio
import logging
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from bs4 import BeautifulSoup

from app.schemas.test_suite import TestSuiteRequest
from app.services.test_suite_service import test_suite_service

logger = logging.getLogger(__name__)

class OraclePatchBotService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False

    def start_bot(self):
        if self.is_running:
            return
        
        # Schedule the bot to check for updates every 24 hours
        # For demonstration purposes, we schedule it to run once immediately after startup in 5 seconds
        self.scheduler.add_job(self.check_for_updates, 'interval', hours=24, id='oracle_patch_check')
        self.scheduler.start()
        self.is_running = True
        logger.info("[OracleBot] Predictive Oracle Patch Analyzer Bot started.")
        
        # Trigger an immediate run asynchronously for demonstration
        asyncio.create_task(self.delayed_first_run())

    async def delayed_first_run(self):
        await asyncio.sleep(5)
        await self.check_for_updates()

    async def check_for_updates(self):
        logger.info("[OracleBot] Waking up to check Oracle Release Notes...")
        
        # 1. Scrape Oracle release notes (Mock implementation)
        impacted_areas = self._scrape_oracle_notes()
        
        if not impacted_areas:
            logger.info("[OracleBot] No relevant changes found in the latest patch.")
            return

        logger.info(f"[OracleBot] Detected changes impacting: {', '.join(impacted_areas)}")

        # 2. Analyze impact and generate a regression suite for the first impacted area
        primary_area = impacted_areas[0]
        logger.info(f"[OracleBot] Generating regression suite for {primary_area}...")
        
        request = TestSuiteRequest(
            process_area=primary_area,
            is_cross_module=True,
            include_negative_tests=True
        )
        
        suite_result = test_suite_service.generate_suite(request)
        
        if suite_result.get("status") == "success":
            suite_name = suite_result.get("suite_name", "Generated Suite")
            logger.info(f"[OracleBot] Successfully generated '{suite_name}' with {len(suite_result.get('execution_steps', []))} steps.")
            # In a full implementation, we would save this to the DB and notify the user via email/slack
        else:
            logger.warning("[OracleBot] Failed to generate regression suite.")

    def analyze_oracle_patch_sync(self, args: dict, session_id: str = "default") -> dict[str, Any]:
        """
        Synchronous entry point used by the Tool Registry / Intent Router
        when the user manually asks to check for Oracle updates.
        """
        logger.info(f"[OracleBot] Manual trigger invoked for session {session_id}.")
        
        impacted_areas = self._scrape_oracle_notes()
        
        if not impacted_areas:
            return {
                "status": "success",
                "tool": "analyze_oracle_patch",
                "message": "Scanned Oracle release notes. No changes impacting our current WinfoTest configurations were found."
            }

        primary_area = impacted_areas[0]
        request = TestSuiteRequest(
            process_area=primary_area,
            is_cross_module=True,
            include_negative_tests=True
        )
        
        suite_result = test_suite_service.generate_suite(request, session_id)
        
        # Override the suite name to make it clear it's from the bot
        if suite_result.get("status") == "success":
            suite_result["suite_name"] = f"Oracle Patch Regression Suite: {primary_area}"
            suite_result["message"] = "I scanned the latest Oracle release notes and identified updates that impact the 'Financials - Procure to Pay' module. I have cross-referenced these updates with your WinfoTest library and generated this targeted regression suite so you can quickly re-test the affected scripts."
            # Change the tool name so the frontend rendering might handle it if we want, or leave it to reuse generate_test_suite UI
            suite_result["tool"] = "generate_test_suite" 
            return suite_result
            
        return {
            "status": "error",
            "tool": "analyze_oracle_patch",
            "message": "Failed to generate regression suite based on Oracle updates."
        }

    def _scrape_oracle_notes(self) -> list[str]:
        """
        Mock implementation of scraping Oracle release notes using beautifulsoup4.
        In a real scenario, this would fetch HTML and parse out the update headers.
        """
        try:
            # Mocking a fetch
            # html = requests.get("https://www.oracle.com/readiness/...").text
            mock_html = '''
            <html>
                <body>
                    <h1>Oracle Cloud Applications 24B Release Notes</h1>
                    <div class="update-section">
                        <h2>Financials</h2>
                        <p>Changes to Invoice Approvals and Procure to Pay workflows.</p>
                    </div>
                </body>
            </html>
            '''
            soup = BeautifulSoup(mock_html, 'html.parser')
            
            impacted_areas = []
            for h2 in soup.find_all('h2'):
                if h2.text.strip() == 'Financials':
                    # Based on paragraph content, extract keywords
                    p = h2.find_next_sibling('p')
                    if p and 'Procure to Pay' in p.text:
                        impacted_areas.append("Procure to Pay")
                        
            return impacted_areas
        except Exception as e:
            logger.error(f"[OracleBot] Error scraping release notes: {e}")
            return []


oracle_patch_bot_service = OraclePatchBotService()
