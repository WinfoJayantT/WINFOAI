-- V015 – Step Data Type & Testing Type
-- Adds data_type and testing_type columns to both step tables with master tables.

-- ── Step Data Type master ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS wt2dev.step_data_type_master (
    data_type_code VARCHAR(50)  PRIMARY KEY,
    data_type_name VARCHAR(255) NOT NULL,
    description    TEXT
);

INSERT INTO wt2dev.step_data_type_master (data_type_code, data_type_name, description) VALUES
    ('ALPHANUMERIC', 'Alphanumeric',       'Letters and numbers combined'),
    ('NUMERIC',      'Numeric',            'Numbers only (integer or decimal)'),
    ('TEXT',         'Free Text',          'Unrestricted text input'),
    ('DATE',         'Date',               'Date value (e.g. DD/MM/YYYY)'),
    ('DATETIME',     'Date & Time',        'Date and time combined'),
    ('EMAIL',        'Email',              'Email address format'),
    ('PHONE',        'Phone Number',       'Phone or mobile number'),
    ('PASSWORD',     'Password',           'Sensitive / masked input field'),
    ('URL',          'URL',                'Web URL starting with http/https'),
    ('BOOLEAN',      'Boolean',            'Yes / No or True / False toggle'),
    ('DROPDOWN',     'Dropdown',           'Selection from a predefined list'),
    ('FILE',         'File Upload',        'File path or file upload input')
ON CONFLICT (data_type_code) DO NOTHING;

-- ── Step Testing Type master ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS wt2dev.step_testing_type_master (
    testing_type_code VARCHAR(50)  PRIMARY KEY,
    testing_type_name VARCHAR(255) NOT NULL,
    description       TEXT
);

INSERT INTO wt2dev.step_testing_type_master (testing_type_code, testing_type_name, description) VALUES
    ('NOT_APPLICABLE', 'Not Applicable',    'No specific testing type assigned to this step'),
    ('SKIP',           'Skip',              'Skip this step during execution'),
    ('CONDITIONAL',    'Conditional',       'Execute this step based on a runtime condition'),
    ('NEGATIVE',       'Negative Testing',  'Test with invalid or boundary values to verify error handling')
ON CONFLICT (testing_type_code) DO NOTHING;

-- ── master_steps ──────────────────────────────────────────────────────────────
ALTER TABLE wt2dev.master_steps
    ADD COLUMN IF NOT EXISTS data_type    VARCHAR(50)  NULL,
    ADD COLUMN IF NOT EXISTS testing_type VARCHAR(50)  NOT NULL DEFAULT 'NOT_APPLICABLE';

-- ── test_run_script_steps ─────────────────────────────────────────────────────
ALTER TABLE wt2dev.test_run_script_steps
    ADD COLUMN IF NOT EXISTS data_type    VARCHAR(50)  NULL,
    ADD COLUMN IF NOT EXISTS testing_type VARCHAR(50)  NOT NULL DEFAULT 'NOT_APPLICABLE';
