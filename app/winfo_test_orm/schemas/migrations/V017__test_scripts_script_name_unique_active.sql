-- V017: Make active (is_deleted = false) script_name values unique on
-- wt2dev.test_scripts.
--
-- Create Script previously only guarded against duplicate names with an
-- application-level check-then-insert (SELECT ... WHERE script_name = X
-- followed by a separate INSERT if not found) — a classic TOCTOU race: two
-- near-simultaneous create requests for the same name (e.g. a UI double
-- submit before the Create button disables) can both pass the check and
-- both insert, producing two active rows with an identical script_name.
-- idx_test_scripts_script_name was only a non-unique index, so nothing at
-- the database layer ever rejected the second insert.
--
-- Safe to re-run: only replaces the index if it isn't already unique.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE schemaname = 'wt2dev'
          AND tablename = 'test_scripts'
          AND indexname = 'idx_test_scripts_script_name'
    ) THEN
        DROP INDEX wt2dev.idx_test_scripts_script_name;
    END IF;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS uk_test_scripts_script_name_active
    ON wt2dev.test_scripts (script_name)
    WHERE NOT is_deleted;
