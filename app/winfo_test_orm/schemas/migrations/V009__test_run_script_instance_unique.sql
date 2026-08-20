-- V009: Guard against two active test_run_scripts silently claiming the same
-- iteration slot for the same source script in the same test run, and make
-- sure removing a script frees its (test_run_id, instance_no) and
-- (test_run_id, execution_order) slots instead of permanently squatting on
-- them.
--
-- This supports running the same script multiple times within a test run
-- (e.g. "Invoice Generation" iteration 1, 2, 3): each iteration is its own
-- test_run_scripts row with a distinct instance_no. The application layer
-- (TestRunScriptRepository._resolve_instance_no) already auto-assigns/
-- validates instance_no before insert/update; this index is the DB-level
-- backstop in case anything ever bypasses that path.
--
-- Verified against a live copy of this schema: both uk_trs_instance and
-- uk_trs_execution_order already exist in some environments, but WITHOUT a
-- partial WHERE clause — meaning a soft-deleted (removed) row permanently
-- blocks its old instance_no/execution_order from ever being reused, instead
-- of freeing it. Confirmed two ways this actually breaks real flows:
--   1. Quick Create reconciliation (Enhancement 2) removing a script and
--      re-adding the same one later (or a different one landing on the
--      removed one's old position) — both deadlock against the leftover
--      soft-deleted row's slot.
--   2. The execution_order case is *not* unique to new code: any existing
--      remove + renumber sequence (e.g. delete a script, then the remaining
--      ones get compacted to 1..N) can land a still-active row on a number
--      a soft-deleted row already holds.
-- This migration upgrades both indexes to their partial form
-- (WHERE NOT is_deleted) so a removed row's old slots become reusable
-- immediately. Safe to re-run: only replaces an index if it isn't already
-- partial.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'test_run_scripts' AND indexname = 'uk_trs_instance'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'test_run_scripts' AND indexname = 'uk_trs_instance'
          AND indexdef ILIKE '%WHERE%'
    ) THEN
        IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uk_trs_instance') THEN
            -- Index backs a table constraint of the same name — can't drop
            -- the index directly; dropping the constraint takes the index
            -- with it.
            ALTER TABLE test_run_scripts DROP CONSTRAINT uk_trs_instance;
        ELSE
            DROP INDEX uk_trs_instance;
        END IF;
    END IF;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS uk_trs_instance
    ON test_run_scripts (test_run_id, source_test_script_id, instance_no)
    WHERE NOT is_deleted;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'test_run_scripts' AND indexname = 'uk_trs_execution_order'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'test_run_scripts' AND indexname = 'uk_trs_execution_order'
          AND indexdef ILIKE '%WHERE%'
    ) THEN
        IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uk_trs_execution_order') THEN
            ALTER TABLE test_run_scripts DROP CONSTRAINT uk_trs_execution_order;
        ELSE
            DROP INDEX uk_trs_execution_order;
        END IF;
    END IF;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS uk_trs_execution_order
    ON test_run_scripts (test_run_id, execution_order)
    WHERE NOT is_deleted;

-- Both indexes are non-deferred, so even within a single transaction two
-- rows can never momentarily share a value while being assigned new ones —
-- TestRunScriptRepository._assign_execution_orders_safely (used by
-- update_execution_orders and reconcile_scripts) reassigns execution_order
-- in two passes (a disjoint negative range, then final values) specifically
-- to avoid that, verified against a live instance of this exact constraint.
