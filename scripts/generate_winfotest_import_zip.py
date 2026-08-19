import json
import csv
import zipfile
import datetime

csv_path = 'Data for project/Employee_onboarding.csv'
with open(csv_path, 'r', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

# Read original exported scripts.json
with zipfile.ZipFile('Data for project/scripts_export.zip', 'r') as z:
    manifest_data = json.loads(z.read('manifest.json').decode('utf-8'))
    scripts_data = json.loads(z.read('scripts.json').decode('utf-8'))

print("Original script definition:")
print(json.dumps(scripts_data[0]['script'], indent=2))

# Build steps array
steps = []
for r in rows:
    sno = int(r['step_no'])
    act = r['action']
    desc = r['step_description']
    param = r['input_parameter'] or ""
    itype = r['input_type'] or "Other"
    loc = r['locator_code'] or ""
    d_val = r['default_value'] or ""
    wait = int(r['wait_ms'] or 0)
    mand = r['is_mandatory'].lower() == 'true'
    
    step_obj = {
        "step_no": sno,
        "action": act,
        "step_description": desc,
        "input_parameter": param,
        "input_type": itype,
        "locator_code": loc,
        "default_value": d_val,
        "wait_ms": wait,
        "is_mandatory": mand,
        "is_active": True,
        "is_manual": False,
        "validation_type": "NOT_APPLICABLE",
        "testing_type": "NOT_APPLICABLE",
        "take_screenshot": True,
        "is_dropdown_open": False,
        "is_option_selection": False,
        "is_unique": False
    }
    steps.append(step_obj)

# Update scripts_data with the 34 steps
scripts_data[0]['steps'] = steps

# Generate new import zip
out_zip_path = 'Data for project/Jayant_intern_ai_ready_to_import.zip'
with zipfile.ZipFile(out_zip_path, 'w', zipfile.ZIP_DEFLATED) as z_out:
    # 1. manifest.json
    manifest_data['exported_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    z_out.writestr('manifest.json', json.dumps(manifest_data, indent=2))
    
    # 2. scripts.json
    z_out.writestr('scripts.json', json.dumps(scripts_data, indent=2))

print(f"\nSuccessfully generated native WinfoTest Import ZIP: {out_zip_path}")
print(f"Packaged {len(steps)} steps into the archive!")
