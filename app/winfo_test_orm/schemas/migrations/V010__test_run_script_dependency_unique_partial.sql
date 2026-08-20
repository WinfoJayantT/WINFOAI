-- V010: Make the (test_run_script_id, depends_on_test_run_script_id) unique
-- constraint on test_run_script_dependencies partial, so removing a
-- dependency (soft-delete) frees that exact pair for reuse instead of
-- permanently blocking it.
--
-- Verified against a live environment: this constraint already exists as
-- a plain (non-partial) UNIQUE (test_run_script_id, depends_on_test_run_script_id),
-- not captured in any tracked schema file (same situation as
-- uk_trs_instance/uk_trs_execution_order on test_run_scripts — see V009).
-- Being non-partial means re-adding a dependency that was previously
-- removed (soft-deleted) permanently fails with a raw IntegrityError
-- instead of succeeding, since the old soft-deleted row still occupies
-- the slot.
--
-- Also addressed at the application layer: TestRunScriptRepository.
-- add_dependency() now checks for an existing *active* duplicate before
-- inserting and returns it idempotently — this migration covers the
-- separate "was removed, now re-adding" case, which a pre-insert active-row
-- check can't catch on its own.
--
-- Safe to re-run: only replaces the constraint/index if it isn't already
-- partial.
DO $$
DECLARE
    existing_conname text;
BEGIN
    SELECT con.conname INTO existing_conname
    FROM pg_constraint con
    JOIN pg_class rel ON rel.oid = con.conrelid
    JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
    WHERE nsp.nspname = 'wt2dev'
      AND rel.relname = 'test_run_script_dependencies'
      AND con.contype = 'u'
      AND pg_get_constraintdef(con.oid) ILIKE '%test_run_script_id%depends_on_test_run_script_id%'
      AND pg_get_constraintdef(con.oid) NOT ILIKE '%WHERE%';

    IF existing_conname IS NOT NULL THEN
        EXECUTE format(
            'ALTER TABLE wt2dev.test_run_script_dependencies DROP CONSTRAINT %I',
            existing_conname
        );
    END IF;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS uk_trsd_script_depends_on
    ON wt2dev.test_run_script_dependencies (test_run_script_id, depends_on_test_run_script_id)
    WHERE NOT is_deleted;
