-- V012: Add is_unique and is_mandatory metadata columns to master_steps and
-- test_run_script_steps.  Safe to re-run: uses IF NOT EXISTS guards.
--
-- is_mandatory: TRUE when the field is required on the Oracle ERP form
--               (detected via required/aria-required attributes or Oracle visual cues).
-- is_unique:    TRUE when the field value must be unique in Oracle
--               (detected via Oracle-specific element metadata or data attributes).
--
-- Both default FALSE so all existing rows are unaffected.

DO $$
BEGIN
    -- ── master_steps ──────────────────────────────────────────────────────────
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'wt2dev'
          AND table_name   = 'master_steps'
          AND column_name  = 'is_mandatory'
    ) THEN
        ALTER TABLE wt2dev.master_steps
            ADD COLUMN is_mandatory BOOLEAN NOT NULL DEFAULT FALSE;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'wt2dev'
          AND table_name   = 'master_steps'
          AND column_name  = 'is_unique'
    ) THEN
        ALTER TABLE wt2dev.master_steps
            ADD COLUMN is_unique BOOLEAN NOT NULL DEFAULT FALSE;
    END IF;

    -- ── test_run_script_steps ─────────────────────────────────────────────────
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'wt2dev'
          AND table_name   = 'test_run_script_steps'
          AND column_name  = 'is_mandatory'
    ) THEN
        ALTER TABLE wt2dev.test_run_script_steps
            ADD COLUMN is_mandatory BOOLEAN NOT NULL DEFAULT FALSE;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'wt2dev'
          AND table_name   = 'test_run_script_steps'
          AND column_name  = 'is_unique'
    ) THEN
        ALTER TABLE wt2dev.test_run_script_steps
            ADD COLUMN is_unique BOOLEAN NOT NULL DEFAULT FALSE;
    END IF;
END $$;
