-- V019: Add playwright_locator_telemetry for the deterministic Redwood-
-- resilient locator layer (pw_step_engine.locators, feature/redwood-resilient-locators).
--
-- Aggregate, observability-only data: which strategy resolved each step's
-- locator (role/label/placeholder/text/test_id/title/css), whether it took
-- a fallback, how many strategies were attempted, and resolution latency.
--
-- Does NOT persist a per-step semantic descriptor (role/name/scope/etc.) —
-- LocatorProfile/LocatorStrategy stay in-memory, rebuilt from
-- locator_code/locator_fallbacks at replay time by legacy_adapter.to_profile().
-- A prior, unrelated attempt at DB-persisted locator/self-heal metadata
-- (structured descriptor threaded through the recording->Kafka->execution
-- pipeline) was fully implemented then explicitly reverted; this table is
-- deliberately narrower in scope than that design.
--
-- No FK constraints to test_run_script_steps — recording-service's inline
-- "Run Now" preview runs can emit telemetry for steps with no persisted
-- test_run_script_step row, and telemetry must never fail to insert because
-- of a missing/unmatched step reference.
CREATE TABLE IF NOT EXISTS wt2dev.playwright_locator_telemetry (
    id                       UUID PRIMARY KEY,
    test_run_id              UUID NULL,
    test_run_script_id       UUID NULL,
    test_run_script_step_id  UUID NULL,
    step_no                  INTEGER NULL,
    strategy_kind            VARCHAR(20) NOT NULL DEFAULT '',
    was_fallback             BOOLEAN NOT NULL DEFAULT FALSE,
    attempts                 INTEGER NOT NULL DEFAULT 1,
    brittle                  BOOLEAN NOT NULL DEFAULT FALSE,
    success                  BOOLEAN NOT NULL DEFAULT TRUE,
    latency_ms               INTEGER NULL,
    error_message            TEXT NULL,
    resolved_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_playwright_locator_telemetry_test_run_script_id
    ON wt2dev.playwright_locator_telemetry (test_run_script_id);

CREATE INDEX IF NOT EXISTS ix_playwright_locator_telemetry_resolved_at
    ON wt2dev.playwright_locator_telemetry (resolved_at);

COMMENT ON TABLE wt2dev.playwright_locator_telemetry IS
    'Observability only: which locator strategy resolved each step, fallback usage, and latency. No per-step semantic descriptor (role/name/scope) is persisted — see pw_step_engine/locators/README.md.';
