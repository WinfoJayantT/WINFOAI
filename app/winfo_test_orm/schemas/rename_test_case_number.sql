-- Migration: rename test_case_number → test_script_number in wt2dev.test_scripts
-- Run this once against your local (and any non-production) database.
-- The ORM model uses `test_script_number`; this aligns the DB column with it.

BEGIN;

-- 1. Rename the column
ALTER TABLE wt2dev.test_scripts
    RENAME COLUMN test_case_number TO test_script_number;

-- 2. Rename the unique constraint (was uk_test_case_number)
ALTER TABLE wt2dev.test_scripts
    RENAME CONSTRAINT uk_test_case_number TO uk_test_script_number;

-- 3. If there is a unique index (separate from the constraint), rename it too.
--    This is only needed if Postgres created an index named differently from the constraint.
--    Run "SELECT indexname FROM pg_indexes WHERE tablename='test_scripts';" to verify.
-- ALTER INDEX wt2dev.uk_test_case_number RENAME TO uk_test_script_number;

COMMIT;
