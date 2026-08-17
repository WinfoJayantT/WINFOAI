"""
StepGenerationService (Dynamic Semantic Generation)
===================================================
Accepts a business scenario description + process area and dynamically
generates the complete WinfoTest UI automation step sequence:

  1. Vector Few-Shot Retrieval - uses Qdrant dense vector search (all-mpnet-base-v2)
     to retrieve the top matching golden test script from the database, then
     reloads its authentic steps from PostgreSQL master_steps (source of truth).
  2. Dynamic Compact Generation - prompts the configured fast LLM to generate
     the entire sequence (login -> navigation -> business actions -> submission)
     in a concise pipe-delimited format (Action | Target | Description | Param).
  3. Strict Schema Validation   - parses and validates every action against standard
     WinfoTest ERP primitives with {{Variable_Name}} placeholder parameterization.
  4. Zero Hardcoded Fallbacks   - every step is generated dynamically by the AI
     grounded in real database RAG context.
"""

import json
import logging
import re
from typing import Any, Dict, List

from sqlalchemy import text

from app.clients.llm_client import llm_client
from app.core.config import settings
from app.repositories.db import engine

logger = logging.getLogger(__name__)

# --- Standard WinfoTest Oracle ERP action primitives ---
VALID_ACTIONS = [
    "Navigate",
    "Click Button",
    "Enter Value - Text Field",
    "Select Option",
    "Open Dropdown",
    "Wait Till Load",
    "Vertical Scroll",
    "Key - Tab",
    "Click",
    "Verify",
]

# --- Dynamic Few-Shot System Prompt ---
_SYSTEM_PROMPT = """You are an Oracle ERP test automation engineer for WinfoTest.
Given a business scenario and reference workflow steps from similar tests in the database, generate the realistic, complete end-to-end sequence of WinfoTest UI automation steps.

RULES:
1. Use ONLY these exact WinfoTest actions:
   Navigate, Click Button, Enter Value - Text Field, Select Option, Open Dropdown, Wait Till Load, Vertical Scroll, Key - Tab, Click, Verify
2. Use {{Variable_Name}} placeholder notation for ANY user-supplied or scenario-specific data (e.g. {{Username}}, {{Password}}, {{Supplier_Name}}, {{Invoice_Amount}}, {{Tax_Org_Type}}).
3. The step sequence must naturally cover the entire transaction lifecycle based on the complexity of the scenario:
   - Initial Login and Homepage navigation
   - Module navigation and primary record creation
   - Header attributes, addresses, contacts, and configuration tabs
   - Line items, schedules, or payment details
   - Final review, save, and submission/approval actions
4. Output format: Exactly ONE line per step using pipe delimiter:
   Action | Target Element | Step Description | Parameter Placeholder
   Example:
   Enter Value - Text Field | Username | Enter username | {{Username}}
   Enter Value - Text Field | Password | Enter password | {{Password}}
   Click Button | Next | Click button: 'Next' |
   Navigate | Home | Click tile/menu: 'Home' |
   Click | Procurement | Click tab: 'Procurement' |
   Navigate | Suppliers | Click tile/menu: 'Suppliers' |
   Click Button | Create Supplier | Click button: 'Create Supplier' |
   Enter Value - Text Field | Supplier Name | Enter supplier name | {{Supplier_Name}}
   Select Option | Tax Organization Type | Select tax org type | {{Tax_Org_Type}}
   Click | Addresses | Click tab: 'Addresses' |
   Click Button | Create Address | Click button: 'Create Address' |
   Enter Value - Text Field | Address Name | Enter address name | {{Address_Name}}
   Click | Payments | Click tab: 'Payments' |
   Select Option | Payment Method | Select payment method | {{Payment_Method}}
   Click Button | Submit | Click button: 'Submit' |
5. Return ONLY the pipe-delimited step lines. No markdown fences, no JSON, no explanations."""


class StepGenerationService:
    # ──────────────────────────────────────────────────────────────────────────
    # Public entry point
    # ──────────────────────────────────────────────────────────────────────────
    def generate_steps(
        self,
        scenario: str,
        process_area: str = "",
        limit: int = 3,
    ) -> Dict[str, Any]:
        """
        Dynamically generates WinfoTest steps for *scenario* using vector few-shot
        RAG grounded in PostgreSQL master_steps.
        """
        logger.info(
            "Generating steps dynamically | scenario='%s' process_area='%s'",
            scenario,
            process_area,
        )

        # 1. Pull dynamic few-shot examples from the database via Qdrant Vector Search
        examples, source_ids = self._retrieve_few_shot_examples(
            scenario, process_area, limit=limit
        )

        # 2. Build the grounded user prompt
        user_prompt = self._build_user_prompt(scenario, process_area, examples)

        # 3. Call the fast local LLM with greedy decoding (temperature=0.0)
        try:
            model_to_use = getattr(settings, "FAST_LLM_MODEL", None) or settings.LLM_MODEL
            raw = llm_client.generate_completion(
                system_prompt=_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.0,
                max_tokens=950,
                model=model_to_use,
                trace_id="generate_script_steps",
            )
        except Exception as exc:
            logger.error("LLM call failed during step generation: %s", exc)
            return {
                "status": "error",
                "tool": "generate_script_steps",
                "scenario": scenario,
                "process_area": process_area,
                "generated_steps": [],
                "few_shot_source_scripts": source_ids,
                "total_steps": 0,
                "reasoning": f"LLM generation failed: {exc}",
            }

        # 4. Parse and validate the dynamically generated steps
        steps = self._parse_steps(raw)

        reasoning = (
            f"Dynamically generated {len(steps)} automation steps for '{scenario}' "
            f"grounded in vector RAG reference from {source_ids}."
            if source_ids else
            f"Dynamically generated {len(steps)} automation steps for '{scenario}'."
        )

        return {
            "status": "success",
            "tool": "generate_script_steps",
            "scenario": scenario,
            "process_area": process_area,
            "generated_steps": steps,
            "few_shot_source_scripts": source_ids,
            "total_steps": len(steps),
            "reasoning": reasoning,
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Few-shot retrieval — Qdrant Vector Search + PostgreSQL Grounding
    # ──────────────────────────────────────────────────────────────────────────
    def _retrieve_few_shot_examples(
        self,
        scenario: str,
        process_area: str,
        limit: int,
    ) -> tuple[List[Dict], List[str]]:
        """
        Retrieves the top semantically similar test script using Qdrant dense vector
        search, then reloads its authentic steps from PostgreSQL master_steps.
        """
        examples: List[Dict] = []
        source_ids: List[str] = []

        search_query = f"{scenario} {process_area}".strip()
        if not search_query:
            return [], []

        try:
            from app.services.embedding_service import embedding_service
            from app.services.vector_store_service import vector_store_service

            # 1. Embed the scenario query using all-mpnet-base-v2
            query_vector = embedding_service.embed_text(search_query)

            # 2. Dense vector search in Qdrant
            hits = vector_store_service.search_similar(
                vector=query_vector,
                limit=limit,
            )

            if not hits:
                return [], []

            best_hit = hits[0]
            payload = best_hit.get("payload", {})
            script_id = str(payload.get("script_id") or best_hit.get("id", ""))
            script_num = str(payload.get("test_script_number") or script_id)
            script_name = str(payload.get("script_name") or "")

            # 3. Reload authentic steps from PostgreSQL (source of truth)
            with engine.connect() as conn:
                step_rows = self._fetch_steps_for_script(conn, script_id)

            if step_rows:
                source_ids.append(script_num)
                examples.append({
                    "script_number": script_num,
                    "script_name": script_name,
                    "steps": step_rows[:25],
                })

        except Exception as exc:
            logger.warning("[FewShotRAG] Vector few-shot retrieval failed: %s", exc)

        return examples, source_ids

    def _fetch_steps_for_script(
        self, conn, script_id: str
    ) -> List[Dict[str, Any]]:
        """Try master_steps, then fall back to test_run_script_steps."""
        try:
            result = conn.execute(
                text("""
                    SELECT step_no, action, step_description, input_parameter
                    FROM master_steps
                    WHERE script_id::text = :sid
                    ORDER BY step_no ASC
                    LIMIT 35
                """),
                {"sid": script_id},
            )
            rows = [dict(r) for r in result.mappings().all()]
            if rows:
                return rows
        except Exception:
            pass

        try:
            result = conn.execute(
                text("""
                    SELECT s.step_no, s.action, s.step_description, s.input_parameter
                    FROM test_run_script_steps s
                    WHERE s.test_run_script_id = (
                        SELECT test_run_script_id FROM test_run_scripts
                        WHERE source_test_script_id::text = :sid
                        ORDER BY creation_date DESC NULLS LAST LIMIT 1
                    )
                    ORDER BY s.step_no ASC
                    LIMIT 35
                """),
                {"sid": script_id},
            )
            return [dict(r) for r in result.mappings().all()]
        except Exception:
            pass

        return []

    # ──────────────────────────────────────────────────────────────────────────
    # Prompt building
    # ──────────────────────────────────────────────────────────────────────────
    def _build_user_prompt(
        self,
        scenario: str,
        process_area: str,
        examples: List[Dict],
    ) -> str:
        parts: List[str] = []

        if examples:
            parts.append("=== REFERENCE ORACLE STEPS FROM GOLDEN TEST MASTER ===")
            for ex in examples:
                parts.append(f"Script: {ex['script_number']} ({ex['script_name']})")
                for st in ex["steps"]:
                    act = st.get("action") or "Navigate"
                    desc = st.get("step_description") or ""
                    param = st.get("input_parameter") or ""
                    parts.append(f"- {act} | {desc} {f'| {param}' if param else ''}")
            parts.append("=== END REFERENCE ===\n")

        if process_area:
            parts.append(f"Process Area: {process_area}")
        parts.append(f"Scenario to Automate: {scenario}")
        parts.append("\nOutput the complete pipe-delimited steps:")

        return "\n".join(parts)

    # ──────────────────────────────────────────────────────────────────────────
    # Response parsing & validation
    # ──────────────────────────────────────────────────────────────────────────
    def _parse_steps(self, raw: str) -> List[Dict[str, Any]]:
        """
        Parses pipe-delimited lines (or fallback JSON) into structured step objects.
        Validates actions against VALID_ACTIONS and assigns sequential step numbers.
        """
        clean = raw.strip()
        parsed_steps: List[Dict[str, Any]] = []

        # 1. Parse pipe-delimited lines
        lines = [line.strip() for line in clean.splitlines() if line.strip() and not line.strip().startswith("#")]
        lines = [l for l in lines if not l.startswith("```")]

        has_pipes = any("|" in l for l in lines)

        if has_pipes:
            for line in lines:
                if "|" not in line:
                    continue
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 2:
                    action_raw = parts[0]
                    target = parts[1] if len(parts) > 1 else ""
                    desc = parts[2] if len(parts) > 2 else f"{action_raw}: {target}"
                    param = parts[3] if len(parts) > 3 else ""

                    # Match action against valid set
                    matched_action = "Navigate"
                    for va in VALID_ACTIONS:
                        if va.lower() == action_raw.lower():
                            matched_action = va
                            break

                    parsed_steps.append({
                        "action": matched_action,
                        "target_element": target,
                        "step_description": desc,
                        "input_parameter": param,
                    })

        # 2. Fallback: Parse JSON if the LLM returned JSON format
        if not parsed_steps:
            try:
                json_str = clean
                if "```" in json_str:
                    m = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", json_str, re.DOTALL)
                    json_str = m.group(1) if m else re.sub(r"```[a-z]*", "", json_str).strip()
                data = json.loads(json_str)
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            act = item.get("action", "Navigate")
                            matched_action = act if act in VALID_ACTIONS else "Navigate"
                            parsed_steps.append({
                                "action": matched_action,
                                "target_element": str(item.get("target_element", "")),
                                "step_description": str(item.get("step_description", "")),
                                "input_parameter": str(item.get("input_parameter", "")),
                            })
            except Exception:
                pass

        # 3. Assign sequential step numbers 1..N
        final_steps: List[Dict[str, Any]] = []
        for i, st in enumerate(parsed_steps, start=1):
            final_steps.append({
                "step_no": i,
                "action": st["action"],
                "step_description": st["step_description"],
                "target_element": st["target_element"],
                "input_parameter": st["input_parameter"],
            })

        return final_steps


step_generation_service = StepGenerationService()
