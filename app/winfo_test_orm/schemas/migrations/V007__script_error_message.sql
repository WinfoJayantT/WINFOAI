-- V007: Add error_message to test_run_scripts for failure diagnostics
-- Safe to re-run: uses IF NOT EXISTS pattern

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'wt2dev'
          AND table_name = 'test_run_scripts'
          AND column_name = 'error_message'
    ) THEN
        ALTER TABLE wt2dev.test_run_scripts ADD COLUMN error_message TEXT;
    END IF;
END $$;
