-- V021: Add locator_path_used to playwright_locator_telemetry.
--
-- E4 fix (recording stability / execution defects): was_fallback already
-- recorded WHETHER a fallback candidate won, but not WHICH one — a step
-- recovered via fallback candidate index 0 was indistinguishable from one
-- recovered via candidate 4, or via self-heal. locator_path_used carries the
-- exact label already computed in-process by pw_step_engine (StepRunner's
-- locator_path_used: "primary" | "fallback:<index>" | "self_heal" | "none")
-- — same scalar-telemetry scope as the rest of this table (see V019), not a
-- semantic descriptor.
ALTER TABLE wt2dev.playwright_locator_telemetry
    ADD COLUMN IF NOT EXISTS locator_path_used VARCHAR(20) NULL;

COMMENT ON COLUMN wt2dev.playwright_locator_telemetry.locator_path_used IS
    'Which locator path actually executed: primary | fallback:<index> | self_heal | none.';
