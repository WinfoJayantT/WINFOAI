-- V013 – Step Validation Metadata
-- Creates step_validation_type_master and adds validation columns to both step tables.

-- ── Step Validation Type master ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS wt2dev.step_validation_type_master (
    validation_type_code VARCHAR(50)  PRIMARY KEY,
    validation_type_name VARCHAR(255) NOT NULL,
    description          TEXT
);

INSERT INTO wt2dev.step_validation_type_master (validation_type_code, validation_type_name, description) VALUES
    ('NOT_APPLICABLE', 'Not Applicable',   'No validation is performed for this step'),
    ('REGEX',          'Regex Validation', 'Validate the step value against a named regex pattern (EMAIL, PHONE_NUMBER, PAN, GST, PIN_CODE, ALPHANUMERIC, NUMERIC_ONLY …)'),
    ('API_VALIDATION', 'API Validation',   'Validate the step value through a named Oracle/API validator (Employee Validation, Supplier Validation …)')
ON CONFLICT (validation_type_code) DO NOTHING;

-- ── master_steps ──────────────────────────────────────────────────────────────
ALTER TABLE wt2dev.master_steps
    ADD COLUMN IF NOT EXISTS validation_type VARCHAR(50)  NOT NULL DEFAULT 'NOT_APPLICABLE',
    ADD COLUMN IF NOT EXISTS validation_name VARCHAR(255);

-- ── test_run_script_steps ─────────────────────────────────────────────────────
ALTER TABLE wt2dev.test_run_script_steps
    ADD COLUMN IF NOT EXISTS validation_type VARCHAR(50)  NOT NULL DEFAULT 'NOT_APPLICABLE',
    ADD COLUMN IF NOT EXISTS validation_name VARCHAR(255);
