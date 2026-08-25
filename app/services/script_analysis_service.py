import logging
from typing import Any

from app.clients.llm_client import LLMTimeoutError, llm_client
from app.core.config import settings

logger = logging.getLogger(__name__)

class ScriptAnalysisService:
    def explain_workflow(self, script_payload: dict[str, Any]) -> dict[str, Any]:
        steps: list[dict[str, Any]] = script_payload.get("steps") or []
        step_summaries = [
            f"Step {step['step_no']}: {step.get('description') or step.get('action') or step.get('step_name')}"
            for step in steps
        ]

        if not settings.is_llm_configured:
            return {
                "status": "service_unavailable",
                "summary": "LLM is not configured. Live database steps are listed below.",
                "workflow_summary": "LLM is not configured. Live database steps are listed below.",
                "step_summaries": step_summaries,
                "llm_used": False,
            }

        # Step Payload Sanitization
        sanitized_steps = [
            {
                "step_no": s.get("step_no"),
                "step_name": s.get("step_name"),
                "action": s.get("action"),
                "description": s.get("description"),
            }
            for s in steps
        ]

        prompt = {
            "script_number": script_payload.get("test_script_number"),
            "script_name": script_payload.get("script_name"),
            "steps": sanitized_steps,
        }

        try:
            model_to_use = getattr(settings, "FAST_LLM_MODEL", None) or settings.LLM_MODEL
            summary = llm_client.generate_completion(
                system_prompt=(
                    "Summarize the ERP test workflow in plain business language in 2-3 concise sentences. "
                    "Use only the provided script metadata and steps."
                ),
                user_prompt=str(prompt),
                temperature=0.0,
                max_tokens=180,
                model=model_to_use,
                trace_id="explain_workflow"
            )
            return {
                "summary": summary.strip(),
                "workflow_summary": summary.strip(),
                "step_summaries": step_summaries,
                "llm_used": True,
            }
        except LLMTimeoutError:
            logger.warning("LLM timed out during explain_workflow")
            return {
                "summary": "Local LLM timed out. Live database steps are listed below.",
                "workflow_summary": "Local LLM timed out. Live database steps are listed below.",
                "step_summaries": step_summaries,
                "llm_used": False,
                "llm_summary_failed": True,
            }
        except Exception as e:
            logger.warning("LLM failed during explain_workflow: %s", e)
            return {
                "status": "internal_error",
                "summary": "LLM encountered an error. Live database steps are listed below.",
                "workflow_summary": "LLM encountered an error. Live database steps are listed below.",
                "step_summaries": step_summaries,
                "llm_used": False,
                "llm_summary_failed": True,
            }

    def _generate_objective(self, script: dict[str, Any], steps: list[dict[str, Any]]) -> str:
        """
        Uses the LLM to synthesise a tight 1-2 sentence business objective for a test script
        when the database `objective` field is null.
        """
        if not getattr(settings, 'LLM_BASE_URL', None) and not getattr(settings, 'LLM_API_KEY', None):
            return script.get('script_name', '')

        # Build a compact step summary — first 8 steps are enough context
        step_lines = []
        for i, s in enumerate(steps[:8], start=1):
            action = s.get('step_action') or s.get('action') or ''
            desc = s.get('step_description') or s.get('description') or ''
            param = s.get('input_parameter') or ''
            line = f"{i}. {action}"
            if desc:
                line += f": {desc}"
            if param:
                line += f" ({param})"
            step_lines.append(line)

        steps_text = '\n'.join(step_lines) if step_lines else 'No steps available.'

        system_prompt = (
            "You are an ERP QA analyst. Write a single, clear, business-facing objective sentence "
            "(max 40 words) that explains what this Oracle ERP test script validates or achieves. "
            "Be specific to the business process — avoid generic phrases like 'this script tests'. "
            "Output only the objective sentence, nothing else."
        )
        user_prompt = (
            f"Script: {script.get('test_script_number', '')} — {script.get('script_name', '')}\n"
            f"Module: {script.get('module', 'Unknown')}\n"
            f"Process: {script.get('process', 'Unknown')}\n"
            f"First steps:\n{steps_text}"
        )

        try:
            model_to_use = getattr(settings, 'FAST_LLM_MODEL', None) or settings.LLM_MODEL
            result = llm_client.generate_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.1,
                max_tokens=80,
                model=model_to_use,
                trace_id='generate_objective'
            )
            return result.strip().strip('"').strip("'")
        except Exception as e:
            logger.warning("LLM objective generation failed: %s", e)
            return script.get('script_name', '')
    def lookup_script(self, identifier: str) -> dict[str, Any]:
        from app.repositories.step_repository import step_repository
        from app.repositories.test_script_repository import test_script_repository
        from app.services.semantic_document_service import semantic_document_service

        script = test_script_repository.get_by_id(identifier)
        if not script:
            return {
                "status": "not_found",
                "message": f"Test script '{identifier}' not found in the database.",
                "reasoning": f"No test_scripts record matches '{identifier}'.",
            }

        steps = step_repository.get_ordered_steps(script["id"])
        doc = semantic_document_service.get_or_create_semantic_document(script, steps)
        script_payload = {**script, "steps": steps}
        
        # Enrich role and objective if missing
        if not script_payload.get("objective") and doc:
            # Extract objective from doc
            import re
            m = re.search(r"### 2\. Functional Objective & Scope\s*\n(.*?)(?=\n###|\Z)", doc, re.DOTALL)
            if m:
                script_payload["objective"] = m.group(1).strip()

        # Final fallback: use LLM to generate objective, or script_name as the very last resort
        if not script_payload.get("objective"):
            generated_obj = self._generate_objective(script_payload, steps)
            script_payload["objective"] = generated_obj if generated_obj else script_payload.get("script_name", "")

        return {
            "status": "success",
            "database_record": script_payload,
            "semantic_document": doc,
            "tool": "filtered_script_lookup",
        }

    def analyze(self, identifier: str) -> dict[str, Any]:
        from app.repositories.step_repository import step_repository
        from app.repositories.test_script_repository import test_script_repository
        from app.services.semantic_document_service import semantic_document_service

        script = test_script_repository.get_by_id(identifier)
        if not script:
            return {
                "status": "not_found",
                "message": f"Test script '{identifier}' not found in the database.",
                "reasoning": f"No test_scripts record matches '{identifier}'.",
            }

        steps = step_repository.get_ordered_steps(script["id"])
        script_payload = {**script, "steps": steps}
        
        doc = semantic_document_service.get_or_create_semantic_document(script, steps)
        
        # Extract fields from the semantic document using regex
        import re
        def extract_field(keyword: str, text: str) -> str:
            # Matches "- **Keyword**: Value" or "Keyword: Value" or "▶ Keyword: Value"
            pattern = rf"(?:^|\n)[ \t]*[-*▶]*\s*(?:\*\*)?{keyword}(?:\*\*)?\s*[:\-]\s*(?:\*\*)?([^\n*]+)(?:\*\*)?"
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                val = match.group(1).strip()
                if val and "not specified" not in val.lower() and "n/a" not in val.lower():
                    return val
            return ""

        extracted_module = extract_field(r"Functional Module", doc) or extract_field(r"Module", doc)
        extracted_process = extract_field(r"Process Area", doc) or extract_field(r"End-to-End Process", doc) or extract_field(r"Process", doc)
        extracted_role = extract_field(r"Assigned Role", doc) or extract_field(r"Role", doc)
        
        # Inject into the payload if they are missing or N/A
        if not script_payload.get("module") or "not specified" in str(script_payload.get("module", "")).lower() or script_payload.get("module") == "N/A":
            if extracted_module:
                script_payload["module"] = extracted_module
                
        if not script_payload.get("process") or "not specified" in str(script_payload.get("process", "")).lower() or script_payload.get("process") == "N/A":
            if extracted_process:
                script_payload["process"] = extracted_process
                
        if not script_payload.get("role") or "not specified" in str(script_payload.get("role", "")).lower() or script_payload.get("role") == "N/A":
            if extracted_role:
                script_payload["role"] = extracted_role
        
        return {
            "status": "success",
            "database_record": script_payload,
            "semantic_document": doc,
            "llm_used": True,
            "tool": "analyze_entity",
        }


script_analysis_service = ScriptAnalysisService()
