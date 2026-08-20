-- =============================================================================
-- Migration V006: Dynamic Cross-Script Data Dependency Framework
-- Creates script_output_parameters and step_input_dependencies tables.
-- Run after renaming test_case_number → test_script_number (rename_test_case_number.sql).
-- =============================================================================

BEGIN;

-- ─────────────────────────────────────────────────────────────────────────────
-- 1. script_output_parameters
--    One row per named runtime value a script step is declared to produce.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS wt2dev.script_output_parameters (
    output_parameter_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_run_script_id      UUID NOT NULL
        REFERENCES wt2dev.test_run_scripts(test_run_script_id),
    source_step_id          UUID
        REFERENCES wt2dev.test_run_script_steps(test_run_script_step_id),
    parameter_name          VARCHAR(255) NOT NULL,
    capture_method          VARCHAR(50)  NOT NULL DEFAULT 'TEXT_CONTENT',
    capture_pattern         VARCHAR(500),
    description             TEXT,
    is_deleted              BOOLEAN NOT NULL DEFAULT FALSE,
    creation_date           TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by              UUID NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sop_script
    ON wt2dev.script_output_parameters(test_run_script_id)
    WHERE NOT is_deleted;

-- Unique parameter names per script (active only)
CREATE UNIQUE INDEX IF NOT EXISTS uq_sop_script_param
    ON wt2dev.script_output_parameters(test_run_script_id, parameter_name)
    WHERE NOT is_deleted;

COMMENT ON TABLE wt2dev.script_output_parameters IS
    'Formally declares that a test-run-script step will capture a named runtime value.';


-- ─────────────────────────────────────────────────────────────────────────────
-- 2. step_input_dependencies
--    One row per (consumer_step → output_parameter) link.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS wt2dev.step_input_dependencies (
    input_dependency_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    consumer_script_id      UUID NOT NULL
        REFERENCES wt2dev.test_run_scripts(test_run_script_id),
    consumer_step_id        UUID NOT NULL
        REFERENCES wt2dev.test_run_script_steps(test_run_script_step_id),
    output_parameter_id     UUID NOT NULL
        REFERENCES wt2dev.script_output_parameters(output_parameter_id),
    parameter_name          VARCHAR(255) NOT NULL,
    target_field            VARCHAR(50)  NOT NULL DEFAULT 'default_value',
    is_deleted              BOOLEAN NOT NULL DEFAULT FALSE,
    creation_date           TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by              UUID NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sid_consumer_script
    ON wt2dev.step_input_dependencies(consumer_script_id)
    WHERE NOT is_deleted;

CREATE INDEX IF NOT EXISTS idx_sid_consumer_step
    ON wt2dev.step_input_dependencies(consumer_step_id)
    WHERE NOT is_deleted;

CREATE INDEX IF NOT EXISTS idx_sid_output_param
    ON wt2dev.step_input_dependencies(output_parameter_id)
    WHERE NOT is_deleted;

-- A step may only declare one dependency per parameter name
CREATE UNIQUE INDEX IF NOT EXISTS uq_sid_step_param
    ON wt2dev.step_input_dependencies(consumer_step_id, parameter_name)
    WHERE NOT is_deleted;

COMMENT ON TABLE wt2dev.step_input_dependencies IS
    'Links a consumer step to a named output produced by another script step.';

COMMIT;
