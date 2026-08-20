-- =====================================================================
-- V024: Kafka reliability & execution flow
--
-- Applied MANUALLY by the database team. Unlike earlier changes, these
-- statements are deliberately NOT mirrored in
-- app/utils/schema_compat.py, so the application will not create them
-- on startup.
--
-- RUN THIS BEFORE DEPLOYING recording-service / execution-service.
-- The ORM models declare both columns; queries against a database
-- without them will fail rather than silently degrade.
--
-- Safe to re-run: every statement is idempotent.
-- Additive only: no column is altered, renamed or dropped, so existing
-- runs, recordings and reports are unaffected.
--
-- Schema below is wt2dev — change the prefix if applying elsewhere.
-- =====================================================================


-- ---------------------------------------------------------------------
-- 1. test_run_scripts.dispatch_attempts
--
-- Durable attempt counter for the bounded automatic retry of scripts
-- that fail to START (Key Vault error, browser-launch crash) before a
-- single step ran. Must be persisted rather than held in memory: the
-- failure being handled is a pod crash/restart, which would reset an
-- in-memory counter to zero and allow unbounded retrying.
--
-- DEFAULT 1, not 0 — every existing row has already had its one real
-- dispatch, so historical scripts start with the correct remaining
-- budget and need no backfill.
-- ---------------------------------------------------------------------
ALTER TABLE wt2dev.test_run_scripts
    ADD COLUMN IF NOT EXISTS dispatch_attempts INTEGER DEFAULT 1;


-- ---------------------------------------------------------------------
-- 2. test_run_script_step_results.skip_reason
--
-- Separates a SKIPPED step's reason from a FAILED step's error_message.
-- The table previously had one column for "why", and every skip path
-- wrote into error_message — making a skipped step structurally
-- indistinguishable from a genuine failure to anything reading it.
--
-- After this change: only FAILED sets error_message, only SKIPPED sets
-- skip_reason.
-- ---------------------------------------------------------------------
ALTER TABLE wt2dev.test_run_script_step_results
    ADD COLUMN IF NOT EXISTS skip_reason TEXT;


-- ---------------------------------------------------------------------
-- 3. One-time backfill for rows written before the split existed.
--
-- Moves an already-SKIPPED row's error_message into skip_reason so
-- historical runs stop reporting false errors too, not just new ones.
-- Idempotent: matches zero rows once error_message has been cleared.
--
-- Touches only rows where execution_status_code = 'SKIPPED'. FAILED and
-- PASSED rows are never read or modified.
-- ---------------------------------------------------------------------
UPDATE wt2dev.test_run_script_step_results
SET skip_reason   = error_message,
    error_message = NULL
WHERE execution_status_code = 'SKIPPED'
  AND error_message IS NOT NULL;


-- ---------------------------------------------------------------------
-- Verification — both should return one row each.
-- ---------------------------------------------------------------------
-- SELECT column_name, data_type, column_default
--   FROM information_schema.columns
--  WHERE table_schema = 'wt2dev'
--    AND (table_name = 'test_run_scripts'             AND column_name = 'dispatch_attempts')
--     OR (table_name = 'test_run_script_step_results' AND column_name = 'skip_reason');
