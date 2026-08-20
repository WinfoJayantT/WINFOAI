-- =============================================================================
-- Recording-Service Runtime Tables — wt2dev schema
-- Run this on any local database to set up the recording-service runtime tables.
-- Requires the wt2dev catalog tables (process_areas, modules, test_scripts)
-- to already exist (apply the main catalog schema first).
--
-- Tables:
--   1. case_number_sequences  — auto-increment counters for test case codes
--   2. master_steps           — recorded steps per test script
--   3. recording_sessions     — live browser recording sessions
--   4. v_script_step_summary  — convenience view over master_steps
-- =============================================================================

-- ── 1. CASE NUMBER SEQUENCES ─────────────────────────────────────────────────
-- Stores one counter row per (process_area, module) combination.
-- Used by CaseNumberService to generate codes like FIN-INV-0042 when a new
-- test script is created.

CREATE TABLE IF NOT EXISTS wt2dev.case_number_sequences
(
    id              UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
    process_area_id UUID    NOT NULL,
    module_id       UUID,
    next_seq        INTEGER NOT NULL DEFAULT 1,

    CONSTRAINT fk_cns_process_area
        FOREIGN KEY (process_area_id)
        REFERENCES wt2dev.process_areas(process_area_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_cns_module
        FOREIGN KEY (module_id)
        REFERENCES wt2dev.modules(module_id)
        ON DELETE SET NULL
);


-- ── 2. MASTER STEPS ──────────────────────────────────────────────────────────
-- One row per recorded Playwright step, linked to a test script.
-- locator_code holds the raw Playwright selector — never exposed to the UI.

CREATE TABLE IF NOT EXISTS wt2dev.master_steps
(
    id                  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    script_id           UUID         NOT NULL,
    step_no             INTEGER      NOT NULL DEFAULT 0,
    step_description    TEXT         NOT NULL DEFAULT '',
    action              VARCHAR(100) NOT NULL DEFAULT 'Action',
    input_parameter     VARCHAR(500),
    input_type          VARCHAR(50),
    locator_code        TEXT,
    default_value       TEXT,
    wait_ms             INTEGER      NOT NULL DEFAULT 0,
    is_dropdown_open    BOOLEAN      NOT NULL DEFAULT FALSE,
    is_option_selection BOOLEAN      NOT NULL DEFAULT FALSE,
    take_screenshot     BOOLEAN      NOT NULL DEFAULT TRUE,
    is_active           BOOLEAN      NOT NULL DEFAULT TRUE,
    is_manual           BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ  DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMPTZ  DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_ms_script
        FOREIGN KEY (script_id)
        REFERENCES wt2dev.test_scripts(test_script_id)
        ON DELETE CASCADE
);

-- Partial unique index: only active steps must have unique step_no per script.
-- Soft-deleted (is_active=false) steps are excluded so their step_no can be reused.
CREATE UNIQUE INDEX IF NOT EXISTS uq_master_step_no_active
    ON wt2dev.master_steps (script_id, step_no) WHERE is_active = true;


-- ── 3. RECORDING SESSIONS ────────────────────────────────────────────────────
-- Tracks an active browser recording session (one per script at a time).

CREATE TABLE IF NOT EXISTS wt2dev.recording_sessions
(
    id               UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    script_id        UUID         NOT NULL,
    session_key      VARCHAR(255) NOT NULL,
    status           VARCHAR(50)  NOT NULL DEFAULT 'active',
    browser          VARCHAR(50)  NOT NULL DEFAULT 'chromium',
    target_url       TEXT         NOT NULL,
    started_at       TIMESTAMPTZ  DEFAULT CURRENT_TIMESTAMP,
    ended_at         TIMESTAMPTZ,
    session_metadata JSONB,

    CONSTRAINT uk_rs_session_key UNIQUE (session_key),

    CONSTRAINT fk_rs_script
        FOREIGN KEY (script_id)
        REFERENCES wt2dev.test_scripts(test_script_id)
        ON DELETE CASCADE
);


-- ── 4. CONVENIENCE VIEW ──────────────────────────────────────────────────────

CREATE OR REPLACE VIEW wt2dev.v_script_step_summary AS
SELECT
    script_id,
    count(*)                          AS total_steps,
    count(*) FILTER (WHERE is_active) AS active_steps,
    min(step_no)                      AS first_step_no,
    max(step_no)                      AS last_step_no
FROM wt2dev.master_steps
GROUP BY script_id;


-- ── 5. OWNERSHIP ─────────────────────────────────────────────────────────────

ALTER TABLE wt2dev.case_number_sequences OWNER TO wtuser_dev;
ALTER TABLE wt2dev.master_steps          OWNER TO wtuser_dev;
ALTER TABLE wt2dev.recording_sessions    OWNER TO wtuser_dev;
ALTER VIEW  wt2dev.v_script_step_summary OWNER TO wtuser_dev;
