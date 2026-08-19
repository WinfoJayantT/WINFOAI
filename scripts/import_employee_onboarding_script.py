import csv
import uuid
from sqlalchemy import text
from app.repositories.db import engine

CSV_PATH = "Data for project/Employee_onboarding.csv"
SCRIPT_ID = uuid.uuid4()
SCRIPT_NUMBER = "HCM.HR.EMP.JAYANT.01"
SCRIPT_NAME = "Jayant_intern_AI"
SCRIPT_DESC = "AI Generated End-to-End Employee Onboarding and Setup Test Script"
OBJECTIVE = "Automate employee onboarding, personal information entry, department assignment, and approval workflow"
MODULE_ID = uuid.UUID("e94ae190-a464-49b3-95d0-d72a26b762d4")

print(f"=== Starting Import of '{SCRIPT_NAME}' ===")
print(f"Target Script ID: {SCRIPT_ID}")

with open(CSV_PATH, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    step_rows = list(reader)

print(f"Loaded {len(step_rows)} steps from {CSV_PATH}")

with engine.begin() as conn:
    # 1. Clean up if previous version with this name exists
    existing = conn.execute(text("SELECT test_script_id FROM test_scripts WHERE script_name = :name"), {"name": SCRIPT_NAME}).fetchall()
    for row in existing:
        old_id = row[0]
        conn.execute(text("DELETE FROM master_steps WHERE script_id = :sid"), {"sid": old_id})
        conn.execute(text("DELETE FROM test_scripts WHERE test_script_id = :sid"), {"sid": old_id})
        print(f"Cleaned up previous version (ID: {old_id})")

    # 2. Insert master test_scripts record
    conn.execute(
        text("""
            INSERT INTO test_scripts (
                test_script_id,
                test_script_number,
                script_name,
                script_description,
                objective,
                module_id,
                status_code,
                version_no,
                is_deleted
            ) VALUES (
                :sid,
                :snum,
                :sname,
                :sdesc,
                :obj,
                :mid,
                'ACTIVE',
                1,
                false
            )
        """),
        {
            "sid": SCRIPT_ID,
            "snum": SCRIPT_NUMBER,
            "sname": SCRIPT_NAME,
            "sdesc": SCRIPT_DESC,
            "obj": OBJECTIVE,
            "mid": MODULE_ID,
        }
    )
    print("Inserted test_scripts master record.")

    # 3. Insert 34 master_steps records
    for row in step_rows:
        step_id = uuid.uuid4()
        step_no = int(row.get("step_no", 1))
        action = row.get("action", "Navigate")
        desc = row.get("step_description", "")
        param = row.get("input_parameter") or None
        itype = row.get("input_type") or "Other"
        locator = row.get("locator_code") or None
        default_val = row.get("default_value") or None
        wait_ms = int(row.get("wait_ms") or 0)
        is_mand = str(row.get("is_mandatory", "true")).lower() == "true"

        conn.execute(
            text("""
                INSERT INTO master_steps (
                    id,
                    script_id,
                    step_no,
                    step_description,
                    action,
                    input_parameter,
                    input_type,
                    locator_code,
                    default_value,
                    wait_ms,
                    is_mandatory,
                    is_active,
                    is_manual,
                    validation_type,
                    testing_type,
                    take_screenshot,
                    is_dropdown_open,
                    is_option_selection,
                    is_unique
                ) VALUES (
                    :id,
                    :sid,
                    :step_no,
                    :desc,
                    :action,
                    :param,
                    :itype,
                    :locator,
                    :default_val,
                    :wait_ms,
                    :is_mand,
                    true,
                    false,
                    'NONE',
                    'FUNCTIONAL',
                    false,
                    false,
                    false,
                    false
                )
            """),
            {
                "id": step_id,
                "sid": SCRIPT_ID,
                "step_no": step_no,
                "desc": desc,
                "action": action,
                "param": param,
                "itype": itype,
                "locator": locator,
                "default_val": default_val,
                "wait_ms": wait_ms,
                "is_mand": is_mand,
            }
        )

    print(f"Successfully inserted all {len(step_rows)} master_steps records.")

print("=== Import Completed Successfully ===")
