-- V011: Add OCI Object Storage columns to test_run_script_step_results.
-- screenshot_b64 is kept (backward compatible) — new executions populate
-- file_path/screenshot_upload_status instead when OCI upload is enabled.
-- Safe to re-run: uses IF NOT EXISTS pattern.

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'wt2dev'
          AND table_name = 'test_run_script_step_results'
          AND column_name = 'file_path'
    ) THEN
        ALTER TABLE wt2dev.test_run_script_step_results ADD COLUMN file_path TEXT;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'wt2dev'
          AND table_name = 'test_run_script_step_results'
          AND column_name = 'screenshot_upload_status'
    ) THEN
        ALTER TABLE wt2dev.test_run_script_step_results ADD COLUMN screenshot_upload_status TEXT;
    END IF;
END $$;
