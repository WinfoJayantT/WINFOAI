-- V020: Add configuration_id to wt2dev.test_scripts.
--
-- Test Scripts previously had no association with a workspace configuration
-- (unlike Test Runs, which have required configuration_id since baseline).
-- Test Script execution (the live edit/replay session — see
-- app/services/step_edit_manager.py) always used settings.ORACLE_ERP_URL
-- from the .env file. This lets a Test Script resolve its Oracle URL from
-- an associated Configuration instead, same as Test Run already does.
--
-- Nullable (unlike test_runs.configuration_id, which is NOT NULL): existing
-- scripts predate this column and have no configuration assigned yet. Null
-- is a legitimate, backward-compatible state — resolution code falls back
-- to settings.ORACLE_ERP_URL when this is null.
--
-- Safe to re-run.
ALTER TABLE wt2dev.test_scripts
    ADD COLUMN IF NOT EXISTS configuration_id uuid;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_test_scripts_configuration_id'
    ) THEN
        ALTER TABLE wt2dev.test_scripts
            ADD CONSTRAINT fk_test_scripts_configuration_id
            FOREIGN KEY (configuration_id)
            REFERENCES wt2dev.workspace_configurations (workspace_configurations_id);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_test_scripts_configuration
    ON wt2dev.test_scripts (configuration_id);
