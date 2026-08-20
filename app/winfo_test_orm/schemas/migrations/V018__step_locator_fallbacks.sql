-- V018: Add locator_fallbacks to master_steps and test_run_script_steps.
--
-- The recorder already computes an ordered list of alternate Playwright
-- locator candidates per step (_locator_builder.build_locator_fallbacks),
-- and the execution runner already knows how to retry with them
-- (StepRunner._execute_step's "Enhancement 8" fallback path) — but neither
-- step table had anywhere to persist the candidate list in between, so the
-- runner never actually received any. This column closes that gap.
--
-- JSON-encoded list[str], most-to-least-stable order; NULL when no
-- fallback candidates were generated (e.g. manually authored steps).
ALTER TABLE wt2dev.master_steps
    ADD COLUMN IF NOT EXISTS locator_fallbacks TEXT NULL;
ALTER TABLE wt2dev.test_run_script_steps
    ADD COLUMN IF NOT EXISTS locator_fallbacks TEXT NULL;

COMMENT ON COLUMN wt2dev.master_steps.locator_fallbacks IS
    'JSON-encoded list[str] of alternate locator strings, most to least stable, tried by the execution runner only after the primary locator_code fails all retries.';
COMMENT ON COLUMN wt2dev.test_run_script_steps.locator_fallbacks IS
    'Copy of master_steps.locator_fallbacks at snapshot time; JSON-encoded list[str].';
