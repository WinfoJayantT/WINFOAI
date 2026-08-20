-- ============================================================================
-- WinfoTest Workbench Full Sync (test_scripts + master_steps)
-- Target: HCM.H2R.HHD.1 - Jayant_intern_ai (ee791d46-4489-40bd-97b0-812cdc20e426)
-- Database: playwright_master | Schema: wt2dev | User: wtadmin
-- ============================================================================

ROLLBACK;
SET search_path TO wt2dev, public;

BEGIN;

-- 1. Ensure test_scripts record exists for this Workbench test case
INSERT INTO test_scripts (
    test_script_id,
    test_script_number,
    script_name,
    script_description,
    objective,
    status_code,
    script_type_code,
    runtime_type_code,
    version_no,
    is_deleted,
    creation_date
) VALUES (
    'ee791d46-4489-40bd-97b0-812cdc20e426',
    'HCM.H2R.HHD.1',
    'Jayant_intern_ai',
    'AI Generated End-to-End Employee Onboarding and Setup Test Script',
    'Automate employee onboarding, personal information entry, department assignment, and approval workflow',
    'PUBLISHED',
    'STANDARD',
    'WEB',
    1,
    false,
    CURRENT_TIMESTAMP
) ON CONFLICT (test_script_id) DO UPDATE 
SET script_name = 'Jayant_intern_ai', test_script_number = 'HCM.H2R.HHD.1';

-- 2. Clean previous draft steps if present
DELETE FROM master_steps WHERE script_id = 'ee791d46-4489-40bd-97b0-812cdc20e426';

-- 3. Insert all 34 automation steps into master_steps
INSERT INTO master_steps (
    id,
    script_id,
    step_no,
    action,
    step_description,
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
    is_unique,
    created_at
) VALUES
    (gen_random_uuid(), 'ee791d46-4489-40bd-97b0-812cdc20e426', 1, 'Navigate', 'Click tile/menu: ''Home''', 'Home', 'Navigate', 'page.get_by_title("Home", exact=True).click()', NULL, 0, true, true, false, 'NOT_APPLICABLE', 'NOT_APPLICABLE', false, false, false, false, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ee791d46-4489-40bd-97b0-812cdc20e426', 2, 'Click', 'Click tab: ''Procurement''', 'Procurement', 'Navigate', 'page.get_by_title("Procurement", exact=True).click()', NULL, 0, true, true, false, 'NOT_APPLICABLE', 'NOT_APPLICABLE', false, false, false, false, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ee791d46-4489-40bd-97b0-812cdc20e426', 3, 'Navigate', 'Click tile/menu: ''Suppliers''', 'Suppliers', 'Navigate', 'page.get_by_title("Suppliers", exact=True).click()', NULL, 0, true, true, false, 'NOT_APPLICABLE', 'NOT_APPLICABLE', false, false, false, false, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ee791d46-4489-40bd-97b0-812cdc20e426', 4, 'Click Button', 'Click button: ''Create Supplier''', 'Create Supplier', 'Button', 'page.get_by_role("button", name="Create Supplier", exact=True).click()', NULL, 0, true, true, false, 'NOT_APPLICABLE', 'NOT_APPLICABLE', false, false, false, false, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ee791d46-4489-40bd-97b0-812cdc20e426', 5, 'Enter Value - Text Field', 'Enter supplier name', 'Supplier Name', 'Textbox', 'page.get_by_role("textbox", name="Supplier Name", exact=True).fill("{value}")', '{{Supplier_Name}}', 0, true, true, false, 'NOT_APPLICABLE', 'NOT_APPLICABLE', false, false, false, false, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ee791d46-4489-40bd-97b0-812cdc20e426', 6, 'Select Option', 'Select tax org type', 'Tax Organization Type', 'Dropdown', 'page.get_by_text("Tax Organization Type", exact=True).click()', '{{Tax_Org_Type}}', 0, true, true, false, 'NOT_APPLICABLE', 'NOT_APPLICABLE', false, false, false, false, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ee791d46-4489-40bd-97b0-812cdc20e426', 7, 'Click', 'Click tab: ''Addresses''', 'Addresses', 'Navigate', 'page.get_by_title("Addresses", exact=True).click()', NULL, 0, true, true, false, 'NOT_APPLICABLE', 'NOT_APPLICABLE', false, false, false, false, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ee791d46-4489-40bd-97b0-812cdc20e426', 8, 'Click Button', 'Click button: ''Create Address''', 'Create Address', 'Button', 'page.get_by_role("button", name="Create Address", exact=True).click()', NULL, 0, true, true, false, 'NOT_APPLICABLE', 'NOT_APPLICABLE', false, false, false, false, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ee791d46-4489-40bd-97b0-812cdc20e426', 9, 'Enter Value - Text Field', 'Enter address name', 'Address Name', 'Textbox', 'page.get_by_role("textbox", name="Address Name", exact=True).fill("{value}")', '{{Address_Name}}', 0, true, true, false, 'NOT_APPLICABLE', 'NOT_APPLICABLE', false, false, false, false, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ee791d46-4489-40bd-97b0-812cdc20e426', 10, 'Click', 'Click tab: ''Payments''', 'Payments', 'Navigate', 'page.get_by_title("Payments", exact=True).click()', NULL, 0, true, true, false, 'NOT_APPLICABLE', 'NOT_APPLICABLE', false, false, false, false, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ee791d46-4489-40bd-97b0-812cdc20e426', 11, 'Select Option', 'Select payment method', 'Payment Method', 'Dropdown', 'page.get_by_text("Payment Method", exact=True).click()', '{{Payment_Method}}', 0, true, true, false, 'NOT_APPLICABLE', 'NOT_APPLICABLE', false, false, false, false, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ee791d46-4489-40bd-97b0-812cdc20e426', 12, 'Click Button', 'Click button: ''Submit''', 'Submit', 'Button', 'page.get_by_role("button", name="Submit", exact=True).click()', NULL, 0, true, true, false, 'NOT_APPLICABLE', 'NOT_APPLICABLE', false, false, false, false, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ee791d46-4489-40bd-97b0-812cdc20e426', 13, 'Click', 'Click tab: ''Employee''', 'Employee', 'Navigate', 'page.get_by_title("Employee", exact=True).click()', NULL, 0, true, true, false, 'NOT_APPLICABLE', 'NOT_APPLICABLE', false, false, false, false, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ee791d46-4489-40bd-97b0-812cdc20e426', 14, 'Click Button', 'Click button: ''Create Employee''', 'Create Employee', 'Button', 'page.get_by_role("button", name="Create Employee", exact=True).click()', NULL, 0, true, true, false, 'NOT_APPLICABLE', 'NOT_APPLICABLE', false, false, false, false, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ee791d46-4489-40bd-97b0-812cdc20e426', 15, 'Enter Value - Text Field', 'Enter employee name', 'Employee Name', 'Textbox', 'page.get_by_role("textbox", name="Employee Name", exact=True).fill("{value}")', '{{Employee_Name}}', 0, true, true, false, 'NOT_APPLICABLE', 'NOT_APPLICABLE', false, false, false, false, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ee791d46-4489-40bd-97b0-812cdc20e426', 16, 'Enter Value - Text Field', 'Enter employee ID', 'Employee ID', 'Textbox', 'page.get_by_role("textbox", name="Employee ID", exact=True).fill("{value}")', '{{Employee_ID}}', 0, true, true, false, 'NOT_APPLICABLE', 'NOT_APPLICABLE', false, false, false, false, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ee791d46-4489-40bd-97b0-812cdc20e426', 17, 'Enter Value - Text Field', 'Enter job title', 'Job Title', 'Textbox', 'page.get_by_role("textbox", name="Job Title", exact=True).fill("{value}")', '{{Job_Title}}', 0, true, true, false, 'NOT_APPLICABLE', 'NOT_APPLICABLE', false, false, false, false, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ee791d46-4489-40bd-97b0-812cdc20e426', 18, 'Enter Value - Text Field', 'Enter department', 'Department', 'Textbox', 'page.get_by_role("textbox", name="Department", exact=True).fill("{value}")', '{{Department}}', 0, true, true, false, 'NOT_APPLICABLE', 'NOT_APPLICABLE', false, false, false, false, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ee791d46-4489-40bd-97b0-812cdc20e426', 19, 'Enter Value - Text Field', 'Enter hire date', 'Hire Date', 'Textbox', 'page.get_by_role("textbox", name="Hire Date", exact=True).fill("{value}")', '{{Hire_Date}}', 0, true, true, false, 'NOT_APPLICABLE', 'NOT_APPLICABLE', false, false, false, false, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ee791d46-4489-40bd-97b0-812cdc20e426', 20, 'Enter Value - Text Field', 'Enter start date', 'Start Date', 'Textbox', 'page.get_by_role("textbox", name="Start Date", exact=True).fill("{value}")', '{{Start_Date}}', 0, true, true, false, 'NOT_APPLICABLE', 'NOT_APPLICABLE', false, false, false, false, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ee791d46-4489-40bd-97b0-812cdc20e426', 21, 'Enter Value - Text Field', 'Enter end date', 'End Date', 'Textbox', 'page.get_by_role("textbox", name="End Date", exact=True).fill("{value}")', '{{End_Date}}', 0, true, true, false, 'NOT_APPLICABLE', 'NOT_APPLICABLE', false, false, false, false, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ee791d46-4489-40bd-97b0-812cdc20e426', 22, 'Enter Value - Text Field', 'Enter email', 'Email', 'Textbox', 'page.get_by_role("textbox", name="Email", exact=True).fill("{value}")', '{{Email}}', 0, true, true, false, 'NOT_APPLICABLE', 'NOT_APPLICABLE', false, false, false, false, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ee791d46-4489-40bd-97b0-812cdc20e426', 23, 'Enter Value - Text Field', 'Enter phone number', 'Phone Number', 'Textbox', 'page.get_by_role("textbox", name="Phone Number", exact=True).fill("{value}")', '{{Phone_Number}}', 0, true, true, false, 'NOT_APPLICABLE', 'NOT_APPLICABLE', false, false, false, false, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ee791d46-4489-40bd-97b0-812cdc20e426', 24, 'Enter Value - Text Field', 'Enter address', 'Address', 'Textbox', 'page.get_by_role("textbox", name="Address", exact=True).fill("{value}")', '{{Address}}', 0, true, true, false, 'NOT_APPLICABLE', 'NOT_APPLICABLE', false, false, false, false, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ee791d46-4489-40bd-97b0-812cdc20e426', 25, 'Enter Value - Text Field', 'Enter city', 'City', 'Textbox', 'page.get_by_role("textbox", name="City", exact=True).fill("{value}")', '{{City}}', 0, true, true, false, 'NOT_APPLICABLE', 'NOT_APPLICABLE', false, false, false, false, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ee791d46-4489-40bd-97b0-812cdc20e426', 26, 'Enter Value - Text Field', 'Enter state', 'State', 'Textbox', 'page.get_by_role("textbox", name="State", exact=True).fill("{value}")', '{{State}}', 0, true, true, false, 'NOT_APPLICABLE', 'NOT_APPLICABLE', false, false, false, false, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ee791d46-4489-40bd-97b0-812cdc20e426', 27, 'Enter Value - Text Field', 'Enter zip code', 'Zip Code', 'Textbox', 'page.get_by_role("textbox", name="Zip Code", exact=True).fill("{value}")', '{{Zip_Code}}', 0, true, true, false, 'NOT_APPLICABLE', 'NOT_APPLICABLE', false, false, false, false, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ee791d46-4489-40bd-97b0-812cdc20e426', 28, 'Enter Value - Text Field', 'Enter country', 'Country', 'Textbox', 'page.get_by_role("textbox", name="Country", exact=True).fill("{value}")', '{{Country}}', 0, true, true, false, 'NOT_APPLICABLE', 'NOT_APPLICABLE', false, false, false, false, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ee791d46-4489-40bd-97b0-812cdc20e426', 29, 'Enter Value - Text Field', 'Enter notes', 'Notes', 'Textbox', 'page.get_by_role("textbox", name="Notes", exact=True).fill("{value}")', '{{Notes}}', 0, true, true, false, 'NOT_APPLICABLE', 'NOT_APPLICABLE', false, false, false, false, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ee791d46-4489-40bd-97b0-812cdc20e426', 30, 'Click Button', 'Click button: ''Save''', 'Save', 'Button', 'page.get_by_role("button", name="Save", exact=True).click()', NULL, 0, true, true, false, 'NOT_APPLICABLE', 'NOT_APPLICABLE', false, false, false, false, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ee791d46-4489-40bd-97b0-812cdc20e426', 31, 'Click', 'Click tab: ''Employee''', 'Employee', 'Navigate', 'page.get_by_title("Employee", exact=True).click()', NULL, 0, true, true, false, 'NOT_APPLICABLE', 'NOT_APPLICABLE', false, false, false, false, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ee791d46-4489-40bd-97b0-812cdc20e426', 32, 'Click Button', 'Click button: ''Approve''', 'Approve', 'Button', 'page.get_by_role("button", name="Approve", exact=True).click()', NULL, 0, true, true, false, 'NOT_APPLICABLE', 'NOT_APPLICABLE', false, false, false, false, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ee791d46-4489-40bd-97b0-812cdc20e426', 33, 'Click', 'Click tab: ''Employee''', 'Employee', 'Navigate', 'page.get_by_title("Employee", exact=True).click()', NULL, 0, true, true, false, 'NOT_APPLICABLE', 'NOT_APPLICABLE', false, false, false, false, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ee791d46-4489-40bd-97b0-812cdc20e426', 34, 'Click Button', 'Click button: ''Disapprove''', 'Disapprove', 'Button', 'page.get_by_role("button", name="Disapprove", exact=True).click()', NULL, 0, true, true, false, 'NOT_APPLICABLE', 'NOT_APPLICABLE', false, false, false, false, CURRENT_TIMESTAMP);

COMMIT;

-- 4. Verification Queries
SELECT test_script_id, test_script_number, script_name, status_code FROM test_scripts WHERE test_script_id = 'ee791d46-4489-40bd-97b0-812cdc20e426';
SELECT step_no, action, input_parameter, default_value, locator_code FROM master_steps WHERE script_id = 'ee791d46-4489-40bd-97b0-812cdc20e426' ORDER BY step_no;