-- =============================================================================
-- TESTRUN SCHEMA — all tables explicitly in wt2dev
-- Safe to run against any connection regardless of search_path.
-- Idempotent: CREATE IF NOT EXISTS + ON CONFLICT DO NOTHING on seed data.
--
-- Creation order (respects FK dependencies):
--   1. run_status_master
--   2. execution_status_master
--   3. validation_status_master
--   4. test_runs
--   5. test_run_scripts
--   6. test_run_script_dependencies
--   7. test_run_script_steps
--   8. test_run_script_step_results
--   9. schedules
--  10. schedule_runs
-- =============================================================================


-- ── 1. MASTER LOOKUP TABLES ──────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS wt2dev.run_status_master
(
    run_status_code             VARCHAR(50)  PRIMARY KEY,
    run_status_name             VARCHAR(100) NOT NULL,
    run_status_description      VARCHAR(500) NOT NULL,
    is_terminal                 BOOLEAN      NOT NULL DEFAULT FALSE,
    display_order               INTEGER      NOT NULL,
    status_code                 VARCHAR(30)  NOT NULL DEFAULT 'PUBLISHED',
    version_no                  INTEGER      NOT NULL DEFAULT 1,
    is_deleted                  BOOLEAN      NOT NULL DEFAULT FALSE,
    deleted_date                TIMESTAMPTZ,
    deleted_by                  UUID,
    creation_date               TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by                  UUID         NOT NULL,
    last_update_date            TIMESTAMPTZ,
    last_updated_by             UUID,

    CONSTRAINT fk_run_status_master_status
        FOREIGN KEY (status_code)
        REFERENCES wt2dev.status_master(status_code)
);

INSERT INTO wt2dev.run_status_master
    (run_status_code, run_status_name, run_status_description, is_terminal, display_order, status_code, version_no, is_deleted, creation_date, created_by)
VALUES
    ('DRAFT',           'Draft',            'Run is being configured and is not yet ready for execution.',                 FALSE, 10, 'PUBLISHED', 1, FALSE, CURRENT_TIMESTAMP, '00000000-0000-0000-0000-000000000000'),
    ('READY_TO_LAUNCH', 'Ready To Launch',  'Run configuration is complete and ready for immediate execution.',           FALSE, 20, 'PUBLISHED', 1, FALSE, CURRENT_TIMESTAMP, '00000000-0000-0000-0000-000000000000'),
    ('SCHEDULED',       'Scheduled',        'Run has been scheduled for future execution.',                               FALSE, 30, 'PUBLISHED', 1, FALSE, CURRENT_TIMESTAMP, '00000000-0000-0000-0000-000000000000'),
    ('PENDING',         'Pending',          'Run start has been requested but execution has not yet been picked up by the Execution Service.', FALSE, 35, 'PUBLISHED', 1, FALSE, CURRENT_TIMESTAMP, '00000000-0000-0000-0000-000000000000'),
    ('IN_PROGRESS',     'In Progress',      'Run execution is currently in progress.',                                    FALSE, 40, 'PUBLISHED', 1, FALSE, CURRENT_TIMESTAMP, '00000000-0000-0000-0000-000000000000'),
    ('PASSED',          'Passed',           'Run completed successfully without any failed test scripts.',                 TRUE,  50, 'PUBLISHED', 1, FALSE, CURRENT_TIMESTAMP, '00000000-0000-0000-0000-000000000000'),
    ('NEEDS_ATTENTION', 'Needs Attention',  'Run completed but one or more test scripts failed or require investigation.', TRUE,  60, 'PUBLISHED', 1, FALSE, CURRENT_TIMESTAMP, '00000000-0000-0000-0000-000000000000'),
    ('CANCELLED',       'Cancelled',        'Run was cancelled before completion.',                                        TRUE,  70, 'PUBLISHED', 1, FALSE, CURRENT_TIMESTAMP, '00000000-0000-0000-0000-000000000000')
ON CONFLICT (run_status_code) DO NOTHING;


CREATE TABLE IF NOT EXISTS wt2dev.execution_status_master
(
    execution_status_code        VARCHAR(50)  PRIMARY KEY,
    execution_status_name        VARCHAR(100) NOT NULL,
    execution_status_description VARCHAR(500) NOT NULL,
    is_terminal                  BOOLEAN      NOT NULL DEFAULT FALSE,
    display_order                INTEGER      NOT NULL,
    status_code                  VARCHAR(30)  NOT NULL DEFAULT 'PUBLISHED',
    version_no                   INTEGER      NOT NULL DEFAULT 1,
    is_deleted                   BOOLEAN      NOT NULL DEFAULT FALSE,
    deleted_date                 TIMESTAMPTZ,
    deleted_by                   UUID,
    creation_date                TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by                   UUID         NOT NULL,
    last_update_date             TIMESTAMPTZ,
    last_updated_by              UUID,

    CONSTRAINT fk_execution_status_master_status
        FOREIGN KEY (status_code)
        REFERENCES wt2dev.status_master(status_code)
);

INSERT INTO wt2dev.execution_status_master
    (execution_status_code, execution_status_name, execution_status_description, is_terminal, display_order, status_code, version_no, is_deleted, creation_date, created_by)
VALUES
    ('PENDING',     'Pending',     'Execution has not started.',                     FALSE, 10, 'PUBLISHED', 1, FALSE, CURRENT_TIMESTAMP, '00000000-0000-0000-0000-000000000000'),
    ('IN_PROGRESS', 'In Progress', 'Execution is currently running.',                FALSE, 20, 'PUBLISHED', 1, FALSE, CURRENT_TIMESTAMP, '00000000-0000-0000-0000-000000000000'),
    ('PAUSED',      'Paused',      'Execution has been paused and can be resumed.',  FALSE, 25, 'PUBLISHED', 1, FALSE, CURRENT_TIMESTAMP, '00000000-0000-0000-0000-000000000000'),
    ('PASSED',      'Passed',      'Execution completed successfully.',              TRUE,  30, 'PUBLISHED', 1, FALSE, CURRENT_TIMESTAMP, '00000000-0000-0000-0000-000000000000'),
    ('FAILED',      'Failed',      'Execution completed with one or more failures.', TRUE,  40, 'PUBLISHED', 1, FALSE, CURRENT_TIMESTAMP, '00000000-0000-0000-0000-000000000000'),
    ('SKIPPED',     'Skipped',     'Execution was intentionally skipped.',           TRUE,  50, 'PUBLISHED', 1, FALSE, CURRENT_TIMESTAMP, '00000000-0000-0000-0000-000000000000'),
    ('CANCELLED',   'Cancelled',   'Execution was cancelled before completion.',     TRUE,  60, 'PUBLISHED', 1, FALSE, CURRENT_TIMESTAMP, '00000000-0000-0000-0000-000000000000')
ON CONFLICT (execution_status_code) DO NOTHING;


CREATE TABLE IF NOT EXISTS wt2dev.validation_status_master
(
    validation_status_code        VARCHAR(50)  PRIMARY KEY,
    validation_status_name        VARCHAR(100) NOT NULL,
    validation_status_description VARCHAR(500) NOT NULL,
    is_terminal                   BOOLEAN      NOT NULL DEFAULT FALSE,
    display_order                 INTEGER      NOT NULL,
    status_code                   VARCHAR(30)  NOT NULL DEFAULT 'PUBLISHED',
    version_no                    INTEGER      NOT NULL DEFAULT 1,
    is_deleted                    BOOLEAN      NOT NULL DEFAULT FALSE,
    deleted_date                  TIMESTAMPTZ,
    deleted_by                    UUID,
    creation_date                 TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by                    UUID         NOT NULL,
    last_update_date              TIMESTAMPTZ,
    last_updated_by               UUID,

    CONSTRAINT fk_validation_status_master_status
        FOREIGN KEY (status_code)
        REFERENCES wt2dev.status_master(status_code)
);

INSERT INTO wt2dev.validation_status_master
    (validation_status_code, validation_status_name, validation_status_description, is_terminal, display_order, status_code, version_no, is_deleted, creation_date, created_by)
VALUES
    ('NOT_VALIDATED', 'Not Validated', 'Validation has not been performed.',                      FALSE, 10, 'PUBLISHED', 1, FALSE, CURRENT_TIMESTAMP, '00000000-0000-0000-0000-000000000000'),
    ('PASSED',        'Passed',        'Validation completed successfully.',                      TRUE,  20, 'PUBLISHED', 1, FALSE, CURRENT_TIMESTAMP, '00000000-0000-0000-0000-000000000000'),
    ('FAILED',        'Failed',        'Validation completed with one or more failures.',         TRUE,  30, 'PUBLISHED', 1, FALSE, CURRENT_TIMESTAMP, '00000000-0000-0000-0000-000000000000'),
    ('WARNING',       'Warning',       'Validation completed with warnings that require review.', TRUE,  40, 'PUBLISHED', 1, FALSE, CURRENT_TIMESTAMP, '00000000-0000-0000-0000-000000000000')
ON CONFLICT (validation_status_code) DO NOTHING;


-- ── 2. CORE RUN TABLES ───────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS wt2dev.test_runs
(
    test_run_id             UUID          PRIMARY KEY DEFAULT gen_random_uuid(),

    workspace_id            UUID          NOT NULL,
    configuration_id        UUID          NOT NULL,

    run_type                VARCHAR(20)   NOT NULL DEFAULT 'RUN',
    template_name           VARCHAR(250),
    template_description    TEXT,

    run_name                VARCHAR(250)  NOT NULL,
    run_description         TEXT,

    run_status_code         VARCHAR(50)   NOT NULL DEFAULT 'DRAFT',

    scheduled_start_time    TIMESTAMPTZ,
    actual_start_time       TIMESTAMPTZ,
    actual_end_time         TIMESTAMPTZ,

    parallel_workers        INTEGER       NOT NULL DEFAULT 1,
    screenshot_mode         VARCHAR(20)   NOT NULL DEFAULT 'on_failure',
    max_retries             INTEGER       NOT NULL DEFAULT 3,
    retry_delay_seconds     INTEGER       NOT NULL DEFAULT 30,

    created_by              UUID          NOT NULL,
    executed_by             UUID,

    version_no              INTEGER       NOT NULL DEFAULT 1,
    is_deleted              BOOLEAN       NOT NULL DEFAULT FALSE,
    deleted_date            TIMESTAMPTZ,
    deleted_by              UUID,

    creation_date           TIMESTAMPTZ   NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_tr_workspace
        FOREIGN KEY (workspace_id)
        REFERENCES wt2dev.workspace(workspace_id),

    CONSTRAINT fk_tr_configuration
        FOREIGN KEY (configuration_id)
        REFERENCES wt2dev.workspace_configurations(workspace_configurations_id),

    CONSTRAINT fk_tr_run_status
        FOREIGN KEY (run_status_code)
        REFERENCES wt2dev.run_status_master(run_status_code),

    CONSTRAINT chk_tr_run_type
        CHECK (run_type IN ('RUN', 'TEMPLATE')),

    CONSTRAINT chk_tr_template_name
        CHECK (
            (run_type = 'RUN')
            OR (run_type = 'TEMPLATE' AND template_name IS NOT NULL)
        ),

    CONSTRAINT chk_tr_screenshot_mode
        CHECK (screenshot_mode IN ('all', 'on_failure', 'none'))
);

CREATE INDEX IF NOT EXISTS idx_tr_workspace        ON wt2dev.test_runs(workspace_id);
CREATE INDEX IF NOT EXISTS idx_tr_configuration    ON wt2dev.test_runs(configuration_id);
CREATE INDEX IF NOT EXISTS idx_tr_run_status       ON wt2dev.test_runs(run_status_code);
CREATE INDEX IF NOT EXISTS idx_tr_run_type         ON wt2dev.test_runs(run_type);
CREATE INDEX IF NOT EXISTS idx_tr_created_by       ON wt2dev.test_runs(created_by);
CREATE INDEX IF NOT EXISTS idx_tr_scheduled_start  ON wt2dev.test_runs(scheduled_start_time);


CREATE TABLE IF NOT EXISTS wt2dev.test_run_scripts
(
    test_run_script_id          UUID          PRIMARY KEY DEFAULT gen_random_uuid(),

    test_run_id                 UUID          NOT NULL,

    source_test_script_id       UUID          NOT NULL,
    source_version_no           INTEGER       NOT NULL,

    instance_no                 INTEGER       NOT NULL DEFAULT 1,
    execution_instance_name     VARCHAR(500),

    test_script_code            VARCHAR(100)  NOT NULL,
    fully_qualified_name        VARCHAR(1000) NOT NULL,
    test_script_name            VARCHAR(500)  NOT NULL,
    test_script_description     TEXT,
    test_objective              TEXT,

    execution_order             INTEGER       NOT NULL,
    validation_status_code      VARCHAR(50)   NOT NULL DEFAULT 'NOT_VALIDATED',
    execution_status_code       VARCHAR(50)   NOT NULL DEFAULT 'PENDING',
    dependency_status_code      VARCHAR(30)   NOT NULL DEFAULT 'NOT_EVALUATED',

    actual_start_time           TIMESTAMPTZ,
    actual_end_time             TIMESTAMPTZ,

    version_no                  INTEGER       NOT NULL DEFAULT 1,
    is_deleted                  BOOLEAN       NOT NULL DEFAULT FALSE,
    deleted_date                TIMESTAMPTZ,
    deleted_by                  UUID,

    creation_date               TIMESTAMPTZ   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by                  UUID          NOT NULL,

    CONSTRAINT fk_trs_run
        FOREIGN KEY (test_run_id)
        REFERENCES wt2dev.test_runs(test_run_id),

    CONSTRAINT fk_trs_source_script
        FOREIGN KEY (source_test_script_id)
        REFERENCES wt2dev.test_scripts(test_script_id),

    CONSTRAINT fk_trs_validation_status
        FOREIGN KEY (validation_status_code)
        REFERENCES wt2dev.validation_status_master(validation_status_code),

    CONSTRAINT fk_trs_execution_status
        FOREIGN KEY (execution_status_code)
        REFERENCES wt2dev.execution_status_master(execution_status_code),

    CONSTRAINT uk_trs_execution_order
        UNIQUE (test_run_id, execution_order),

    CONSTRAINT uk_trs_instance
        UNIQUE (test_run_id, source_test_script_id, instance_no),

    CONSTRAINT chk_trs_instance
        CHECK (instance_no > 0),

    CONSTRAINT chk_trs_dependency_status
        CHECK (dependency_status_code IN ('NOT_EVALUATED', 'WAITING', 'SATISFIED', 'BLOCKED'))
);

CREATE INDEX IF NOT EXISTS idx_trs_run               ON wt2dev.test_run_scripts(test_run_id);
CREATE INDEX IF NOT EXISTS idx_trs_source_script     ON wt2dev.test_run_scripts(source_test_script_id);
CREATE INDEX IF NOT EXISTS idx_trs_execution_status  ON wt2dev.test_run_scripts(execution_status_code);
CREATE INDEX IF NOT EXISTS idx_trs_validation_status ON wt2dev.test_run_scripts(validation_status_code);


CREATE TABLE IF NOT EXISTS wt2dev.test_run_script_dependencies
(
    test_run_script_dependency_id    UUID        PRIMARY KEY DEFAULT gen_random_uuid(),

    test_run_script_id               UUID        NOT NULL,
    depends_on_test_run_script_id    UUID        NOT NULL,

    dependency_source                VARCHAR(20) NOT NULL,
    source_test_script_dependency_id UUID,

    version_no                       INTEGER     NOT NULL DEFAULT 1,
    is_deleted                       BOOLEAN     NOT NULL DEFAULT FALSE,
    deleted_date                     TIMESTAMPTZ,
    deleted_by                       UUID,

    creation_date                    TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by                       UUID        NOT NULL,

    CONSTRAINT fk_trsd_script
        FOREIGN KEY (test_run_script_id)
        REFERENCES wt2dev.test_run_scripts(test_run_script_id),

    CONSTRAINT fk_trsd_depends_on
        FOREIGN KEY (depends_on_test_run_script_id)
        REFERENCES wt2dev.test_run_scripts(test_run_script_id),

    CONSTRAINT uk_trsd_dependency
        UNIQUE (test_run_script_id, depends_on_test_run_script_id),

    CONSTRAINT chk_trsd_not_self
        CHECK (test_run_script_id <> depends_on_test_run_script_id),

    CONSTRAINT chk_trsd_source
        CHECK (dependency_source IN ('LIBRARY', 'RUN'))
);

CREATE INDEX IF NOT EXISTS idx_trsd_script     ON wt2dev.test_run_script_dependencies(test_run_script_id);
CREATE INDEX IF NOT EXISTS idx_trsd_depends_on ON wt2dev.test_run_script_dependencies(depends_on_test_run_script_id);


-- ── 3. STEP-LEVEL EXECUTION ───────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS wt2dev.test_run_script_steps
(
    test_run_script_step_id UUID         PRIMARY KEY DEFAULT gen_random_uuid(),

    test_run_script_id      UUID         NOT NULL,
    source_master_step_id   UUID,

    step_no                 INTEGER      NOT NULL,
    step_description        TEXT         NOT NULL DEFAULT '',
    action                  VARCHAR(100) NOT NULL DEFAULT 'Action',
    input_parameter         VARCHAR(500),
    input_type              VARCHAR(50),
    locator_code            TEXT,
    default_value           TEXT,
    wait_ms                 INTEGER      NOT NULL DEFAULT 0,
    take_screenshot         BOOLEAN      NOT NULL DEFAULT TRUE,
    is_active               BOOLEAN      NOT NULL DEFAULT TRUE,
    is_manual               BOOLEAN      NOT NULL DEFAULT FALSE,
    is_injected             BOOLEAN      NOT NULL DEFAULT FALSE,
    is_modified             BOOLEAN      NOT NULL DEFAULT FALSE,

    version_no              INTEGER      NOT NULL DEFAULT 1,
    is_deleted              BOOLEAN      NOT NULL DEFAULT FALSE,
    deleted_date            TIMESTAMPTZ,
    deleted_by              UUID,

    creation_date           TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by              UUID         NOT NULL,
    last_update_date        TIMESTAMPTZ,
    last_updated_by         UUID,

    CONSTRAINT fk_trss_script
        FOREIGN KEY (test_run_script_id)
        REFERENCES wt2dev.test_run_scripts(test_run_script_id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_trss_script_step_no ON wt2dev.test_run_script_steps(test_run_script_id, step_no);


CREATE TABLE IF NOT EXISTS wt2dev.test_run_script_step_results
(
    test_run_script_step_result_id UUID         PRIMARY KEY DEFAULT gen_random_uuid(),

    test_run_script_step_id        UUID         NOT NULL,
    test_run_script_id             UUID         NOT NULL,
    attempt_no                     INTEGER      NOT NULL DEFAULT 1,

    step_no                        INTEGER      NOT NULL,
    step_description               VARCHAR(500),
    action                         VARCHAR(100),
    input_parameter                VARCHAR(500),
    input_value                    TEXT,

    execution_status_code          VARCHAR(50)  NOT NULL DEFAULT 'PENDING',

    started_at                     TIMESTAMPTZ,
    ended_at                       TIMESTAMPTZ,
    duration_ms                    INTEGER,
    retry_count                    INTEGER      NOT NULL DEFAULT 0,

    screenshot_b64                 TEXT,
    error_message                  TEXT,
    executed_locator               TEXT,

    creation_date                  TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by                     UUID         NOT NULL,

    CONSTRAINT fk_trssr_step
        FOREIGN KEY (test_run_script_step_id)
        REFERENCES wt2dev.test_run_script_steps(test_run_script_step_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_trssr_script
        FOREIGN KEY (test_run_script_id)
        REFERENCES wt2dev.test_run_scripts(test_run_script_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_trssr_execution_status
        FOREIGN KEY (execution_status_code)
        REFERENCES wt2dev.execution_status_master(execution_status_code)
);

CREATE INDEX IF NOT EXISTS idx_trssr_script ON wt2dev.test_run_script_step_results(test_run_script_id);
CREATE INDEX IF NOT EXISTS idx_trssr_step   ON wt2dev.test_run_script_step_results(test_run_script_step_id);


-- ── 4. SCHEDULING ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS wt2dev.schedules
(
    schedule_id             UUID          PRIMARY KEY DEFAULT gen_random_uuid(),

    test_run_id             UUID          NOT NULL,

    schedule_name           VARCHAR(255)  NOT NULL,
    schedule_description    TEXT,

    cron_expression         VARCHAR(100),
    scheduled_at            TIMESTAMPTZ,
    timezone                VARCHAR(50)   NOT NULL DEFAULT 'UTC',

    is_enabled              BOOLEAN       NOT NULL DEFAULT TRUE,

    last_run_at             TIMESTAMPTZ,
    last_run_status_code    VARCHAR(50),
    next_run_at             TIMESTAMPTZ,
    run_count               INTEGER       NOT NULL DEFAULT 0,

    version_no              INTEGER       NOT NULL DEFAULT 1,
    is_deleted              BOOLEAN       NOT NULL DEFAULT FALSE,
    deleted_date            TIMESTAMPTZ,
    deleted_by              UUID,

    creation_date           TIMESTAMPTZ   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by              UUID          NOT NULL,
    last_update_date        TIMESTAMPTZ,
    last_updated_by         UUID,

    CONSTRAINT fk_sch_test_run
        FOREIGN KEY (test_run_id)
        REFERENCES wt2dev.test_runs(test_run_id),

    CONSTRAINT fk_sch_last_run_status
        FOREIGN KEY (last_run_status_code)
        REFERENCES wt2dev.run_status_master(run_status_code),

    CONSTRAINT chk_sch_trigger
        CHECK (cron_expression IS NOT NULL OR scheduled_at IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS idx_sch_test_run ON wt2dev.schedules(test_run_id);
CREATE INDEX IF NOT EXISTS idx_sch_enabled  ON wt2dev.schedules(is_enabled);
CREATE INDEX IF NOT EXISTS idx_sch_next_run ON wt2dev.schedules(next_run_at);


CREATE TABLE IF NOT EXISTS wt2dev.schedule_runs
(
    schedule_run_id     UUID        PRIMARY KEY DEFAULT gen_random_uuid(),

    schedule_id         UUID        NOT NULL,
    test_run_id         UUID,

    run_status_code     VARCHAR(50),

    started_at          TIMESTAMPTZ,
    ended_at            TIMESTAMPTZ,
    error_message       TEXT,

    creation_date       TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by          UUID        NOT NULL,

    CONSTRAINT fk_schr_schedule
        FOREIGN KEY (schedule_id)
        REFERENCES wt2dev.schedules(schedule_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_schr_test_run
        FOREIGN KEY (test_run_id)
        REFERENCES wt2dev.test_runs(test_run_id),

    CONSTRAINT fk_schr_run_status
        FOREIGN KEY (run_status_code)
        REFERENCES wt2dev.run_status_master(run_status_code)
);

CREATE INDEX IF NOT EXISTS idx_schr_schedule ON wt2dev.schedule_runs(schedule_id);


-- ── 5. OWNERSHIP ─────────────────────────────────────────────────────────────

ALTER TABLE wt2dev.run_status_master            OWNER TO wtuser_dev;
ALTER TABLE wt2dev.execution_status_master      OWNER TO wtuser_dev;
ALTER TABLE wt2dev.validation_status_master     OWNER TO wtuser_dev;
ALTER TABLE wt2dev.test_runs                    OWNER TO wtuser_dev;
ALTER TABLE wt2dev.test_run_scripts             OWNER TO wtuser_dev;
ALTER TABLE wt2dev.test_run_script_dependencies OWNER TO wtuser_dev;
ALTER TABLE wt2dev.test_run_script_steps        OWNER TO wtuser_dev;
ALTER TABLE wt2dev.test_run_script_step_results OWNER TO wtuser_dev;
ALTER TABLE wt2dev.schedules                    OWNER TO wtuser_dev;
ALTER TABLE wt2dev.schedule_runs                OWNER TO wtuser_dev;
