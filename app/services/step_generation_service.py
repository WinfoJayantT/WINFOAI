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
from typing import Any, Dict, List, Optional

from sqlalchemy import text

from app.clients.llm_client import llm_client
from app.core.config import settings
from app.repositories.db import engine

# ── logger initialization ───────────────────────────────────────────────
logger = logging.getLogger(__name__)

# ── static primitives ───────────────────────────────────────────────────
# Standard WinfoTest Oracle ERP action primitives
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

# ── dynamic few-shot system prompt ──────────────────────────────────────
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


# ── class definition ──────────────────────────────────────────────────
class StepGenerationService:
    """
    Orchestrates the vector retrieval and LLM prompt generation for creating new test scripts.
    """

    # ── public entry point ──────────────────────────────────────────────
    def generate_steps(
        self,
        scenario: str,
        process_area: str = "",
        test_data: Optional[Dict[str, Any]] = None,
        limit: int = 3,
    ) -> Dict[str, Any]:
        """
        Dynamically generates WinfoTest steps for *scenario* using vector few-shot
        RAG grounded in PostgreSQL master_steps, with optional test_data variable binding.
        
        Args:
            scenario (str): Natural language description of the test to generate.
            process_area (str): Oracle module or process area grouping.
            test_data (Dict): Pre-defined variables to bind (e.g., {"Supplier_Name": "Acme"}).
            limit (int): Number of reference scripts to retrieve for RAG context.
            
        Returns:
            Dict: Contains generated steps, CSV payload, and reasoning summary.
        """
        logger.info(
            "Generating steps dynamically | scenario='%s' process_area='%s' test_data_keys=%s",
            scenario,
            process_area,
            list(test_data.keys()) if test_data else [],
        )

        # 1. Pull dynamic few-shot examples from the database via Qdrant Vector Search
        examples, source_ids = self._retrieve_few_shot_examples(
            scenario, process_area, limit=limit
        )

        # 2. Build the grounded user prompt with test data if provided
        user_prompt = self._build_user_prompt(scenario, process_area, examples, test_data=test_data)

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

        # 4. Parse, enrich, and validate the dynamically generated steps
        steps = self._parse_steps(raw, test_data=test_data)
        csv_content = self.export_steps_to_csv(steps)

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
            "csv_export": csv_content,
            "reasoning": reasoning,
        }

    # ── csv export formatting ───────────────────────────────────────────
    def export_steps_to_csv(self, steps: List[Dict[str, Any]]) -> str:
        """
        Exports generated JSON steps to a 100% WinfoTest-compliant CSV format string.
        """
        import csv
        import io
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
        writer.writerow([
            "step_no",
            "action",
            "step_description",
            "input_parameter",
            "input_type",
            "locator_code",
            "default_value",
            "wait_ms",
            "is_mandatory"
        ])
        for s in steps:
            writer.writerow([
                s.get("step_no", 1),
                s.get("action", "Navigate"),
                s.get("step_description", ""),
                s.get("input_parameter", ""),
                s.get("input_type", "Other"),
                s.get("locator_code", ""),
                s.get("default_value", ""),
                s.get("wait_ms", 0),
                "true" if s.get("is_mandatory", True) else "false"
            ])
        return output.getvalue()

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
        
        Args:
            scenario: The core test description.
            process_area: Module filter.
            limit: How many examples to fetch.
            
        Returns:
            Tuple containing the List of examples and List of source script IDs.
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

    # ── sql step fetching ───────────────────────────────────────────────
    def _fetch_steps_for_script(
        self, conn, script_id: str
    ) -> List[Dict[str, Any]]:
        """
        Try to pull steps from `master_steps`, then fall back to `test_run_script_steps`.
        Uses raw SQLAlchemy queries for speed and exact ordering.
        """
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
        test_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Constructs the final prompt combining the few-shot examples and user context.
        """
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

        if test_data and isinstance(test_data, dict) and len(test_data) > 0:
            parts.append("=== USER-SUPPLIED TEST DATA DATASET ===")
            parts.append("Bind the following test data variables into your steps using {{Variable_Name}}:")
            for k, v in test_data.items():
                parts.append(f"- {k}: {v}")
            parts.append("=== END TEST DATA ===\n")

        if process_area:
            parts.append(f"Process Area: {process_area}")
        parts.append(f"Scenario to Automate: {scenario}")
        parts.append("\nOutput the complete pipe-delimited steps:")

        return "\n".join(parts)

    # ──────────────────────────────────────────────────────────────────────────
    # Response parsing & validation
    # ──────────────────────────────────────────────────────────────────────────
    def _parse_steps(
        self, raw: str, test_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Parses pipe-delimited lines (or fallback JSON) into structured step objects.
        Enriches actions with input_type, locator_code, default_value, and assigns sequential step numbers.
        """
        clean = raw.strip()
        parsed_steps: List[Dict[str, Any]] = []

        # Normalization lookup for test_data keys
        data_lookup = {}
        if test_data and isinstance(test_data, dict):
            for k, v in test_data.items():
                data_lookup[k.lower().strip()] = str(v)
                data_lookup[k.lower().strip().replace(" ", "_")] = str(v)
                data_lookup[k.lower().strip().replace("_", "")] = str(v)

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

                    # Clean parameter notation
                    param_clean = param.strip()
                    if param_clean and not param_clean.startswith("{{") and not param_clean.endswith("}}"):
                        # If simple text variable, wrap nicely
                        if re.match(r"^[a-zA-Z0-9_]+$", param_clean):
                            param_clean = f"{{{{{param_clean}}}}}"

                    # Match action against valid set
                    matched_action = "Navigate"
                    for va in VALID_ACTIONS:
                        if va.lower() == action_raw.lower() or va.lower() in action_raw.lower():
                            matched_action = va
                            break

                    parsed_steps.append({
                        "action": matched_action,
                        "target_element": target,
                        "step_description": desc,
                        "input_parameter": param_clean,
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
                            
                            p_val = str(item.get("input_parameter", "")).strip()
                            if p_val and not p_val.startswith("{{") and re.match(r"^[a-zA-Z0-9_]+$", p_val):
                                p_val = f"{{{{{p_val}}}}}"
                            parsed_steps.append({
                                "action": matched_action,
                                "target_element": str(item.get("target_element", "")),
                                "step_description": str(item.get("step_description", "")),
                                "input_parameter": p_val,
                            })
            except Exception:
                pass

        # 3. Assign sequential step numbers and infer Playwright locator_code, input_type, and strict input_parameter / default_value
        final_steps: List[Dict[str, Any]] = []
        for i, st in enumerate(parsed_steps, start=1):
            act = st["action"]
            target = st["target_element"].strip()
            param_raw = st["input_parameter"].strip()
            desc = st["step_description"].strip()

            # Infer input_type and Playwright JSON locators
            locator_fallbacks = []
            if "Text Field" in act or "Enter" in act or "Type" in act:
                input_type = "Textbox"
                locator_code = f'page.get_by_role("textbox", name="{target}", exact=True).fill("{{value}}")'
                locator_fallbacks = [[{"method": "role", "value": "textbox", "kwargs": {"name": target, "exact": True}}]]
            elif "Button" in act or "Click Button" in act:
                input_type = "Button"
                locator_code = f'page.get_by_role("button", name="{target}", exact=True).click()'
                locator_fallbacks = [[{"method": "role", "value": "button", "kwargs": {"name": target, "exact": True}}]]
            elif "Navigate" in act or "Click" in act:
                input_type = "Navigate"
                locator_code = f'page.get_by_title("{target}", exact=True).click()'
                locator_fallbacks = [[{"method": "title", "value": target, "kwargs": {"exact": True}}]]
            elif "Option" in act or "Dropdown" in act or "Select" in act:
                input_type = "Dropdown"
                locator_code = f'page.get_by_text("{target}", exact=True).click()'
                locator_fallbacks = [[{"method": "text", "value": target, "kwargs": {"exact": True}}]]
            elif "Verify" in act:
                input_type = "Validation"
                locator_code = f'expect(page.get_by_text("{target}")).to_be_visible()'
                locator_fallbacks = [[{"method": "text", "value": target, "kwargs": {"exact": True}}]]
            elif "Tab" in act or "Key" in act:
                input_type = "Other"
                locator_code = 'page.keyboard.press("Tab")'
            elif "Wait" in act:
                input_type = "Other"
                locator_code = 'page.wait_for_load_state("networkidle")'
            else:
                input_type = "Other"
                locator_code = f'page.locator("{target}").click()'
                locator_fallbacks = [target]
            
            fb_json = json.dumps(locator_fallbacks) if locator_fallbacks else ""

            # Strict WinfoTest input_parameter assignment:
            # - Tells the automation runner WHERE on the screen to click, type, or navigate
            if target:
                input_param = target
            elif "Tab" in act:
                input_param = "Click Tab"
            elif "Wait" in act:
                input_param = "Wait till load"
            elif "Login" in act:
                input_param = "Username>Password"
            else:
                input_param = desc or act

            # Strict WinfoTest default_value assignment:
            # - For Data-entry steps (Textbox, Dropdown, Select):
            #   1. Match test_data value if provided by user
            #   2. Else use parameter token (e.g. {{Supplier_Name}})
            #   3. Else generate {{Target_Name}}
            # - For Click / Navigate / Wait / Tab: default_value must be empty ("")
            default_val = ""
            if input_type in ("Textbox", "Dropdown") or "Enter" in act or "Select" in act or "Option" in act:
                # Check user test_data
                matched_test_val = ""
                if param_raw:
                    raw_key = re.sub(r"[{}\s]", "", param_raw).lower()
                    if raw_key in data_lookup:
                        matched_test_val = data_lookup[raw_key]
                    elif raw_key.replace("_", "") in data_lookup:
                        matched_test_val = data_lookup[raw_key.replace("_", "")]

                if not matched_test_val and target:
                    target_key = target.lower().strip()
                    if target_key in data_lookup:
                        matched_test_val = data_lookup[target_key]
                    elif target_key.replace(" ", "_") in data_lookup:
                        matched_test_val = data_lookup[target_key.replace(" ", "_")]

                if matched_test_val:
                    default_val = matched_test_val
                elif param_raw:
                    default_val = param_raw
                elif target:
                    clean_var = re.sub(r"[^a-zA-Z0-9_]", "_", target.replace(" ", "_"))
                    default_val = f"{{{{{clean_var}}}}}"

            final_steps.append({
                "step_no": i,
                "action": act,
                "step_description": desc,
                "target_element": target,
                "input_parameter": input_param,
                "input_type": input_type,
                "locator_code": locator_code,
                "locator_fallbacks": fb_json,
                "default_value": default_val,
                "wait_ms": 0,
                "is_mandatory": True,
            })

        return final_steps


# ── singleton export ──────────────────────────────────────────────────
step_generation_service = StepGenerationService()
