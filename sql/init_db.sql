-- ============================================================================
-- LOCAL DEV BOOTSTRAP SCHEMA ONLY.
-- PROJECT_CONTEXT_FINAL.md section 4: "Mock data may exist only for local unit
-- testing and early development." This file exists so `docker compose up` gives
-- you a working PostgreSQL to point the app at. It is NOT the real WinfoTest
-- schema. When you connect to the actual WinfoTest database, point
-- DATABASE_URL / DATABASE_SCHEMA at that instance instead and do not rely on
-- this file for production shape.
-- ============================================================================

CREATE TABLE IF NOT EXISTS process_areas (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS processes (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    process_area_id INTEGER REFERENCES process_areas(id)
);

CREATE TABLE IF NOT EXISTS modules (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS labels (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    display_name TEXT
);

CREATE TABLE IF NOT EXISTS test_scripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_script_number TEXT NOT NULL UNIQUE,
    qualified_name TEXT,
    script_name TEXT NOT NULL,
    description TEXT,
    objective TEXT,
    module_id INTEGER REFERENCES modules(id),
    process_id INTEGER REFERENCES processes(id),
    role_id INTEGER REFERENCES roles(id),
    owner_user_id INTEGER REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS test_script_labels (
    test_script_id UUID REFERENCES test_scripts(id) ON DELETE CASCADE,
    label_id INTEGER REFERENCES labels(id) ON DELETE CASCADE,
    PRIMARY KEY (test_script_id, label_id)
);

CREATE TABLE IF NOT EXISTS test_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ,
    status TEXT
);

CREATE TABLE IF NOT EXISTS test_run_scripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_run_id UUID REFERENCES test_runs(id) ON DELETE CASCADE,
    test_script_id UUID REFERENCES test_scripts(id) ON DELETE CASCADE,
    status TEXT,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS test_run_script_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_run_script_id UUID REFERENCES test_run_scripts(id) ON DELETE CASCADE,
    step_no INTEGER NOT NULL,
    step_action TEXT,
    step_description TEXT,
    input_parameter TEXT,
    default_value TEXT,
    locator_code TEXT,
    fallback_locator_code TEXT
);

CREATE TABLE IF NOT EXISTS test_run_script_step_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_run_script_step_id UUID REFERENCES test_run_script_steps(id) ON DELETE CASCADE,
    status TEXT NOT NULL,
    error_message TEXT,
    dom_snapshot TEXT,
    executed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- AI-owned tables (section 29) — kept separate from WinfoTest core tables.
CREATE TABLE IF NOT EXISTS ai_semantic_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_script_id UUID REFERENCES test_scripts(id) ON DELETE CASCADE,
    semantic_document TEXT NOT NULL,
    generated_by TEXT NOT NULL, -- 'llm' | 'deterministic_fallback'
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ai_vector_index_status (
    test_script_id UUID PRIMARY KEY REFERENCES test_scripts(id) ON DELETE CASCADE,
    embedding_model TEXT NOT NULL,
    embedding_dimension INTEGER NOT NULL,
    indexed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    source_updated_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS ai_conversation_sessions (
    session_id TEXT PRIMARY KEY,
    state_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ai_tool_audit_logs (
    audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "timestamp" TIMESTAMPTZ NOT NULL DEFAULT now(),
    session_id TEXT,
    user_id TEXT,
    intent TEXT,
    tool_name TEXT NOT NULL,
    arguments_json JSONB,
    status TEXT NOT NULL,
    records_returned INTEGER,
    duration_ms INTEGER,
    error_message TEXT,
    trace_id TEXT
);

-- Minimal seed data so the app has something to query on first run.
INSERT INTO process_areas (name) VALUES ('Financials') ON CONFLICT DO NOTHING;
INSERT INTO processes (name, process_area_id)
  SELECT 'Procure to Pay (P2P)', id FROM process_areas WHERE name = 'Financials'
  ON CONFLICT DO NOTHING;
INSERT INTO modules (name) VALUES ('Accounts Payable (AP)') ON CONFLICT DO NOTHING;
INSERT INTO roles (name) VALUES ('Accounts Payable Specialist') ON CONFLICT DO NOTHING;

INSERT INTO test_scripts (test_script_number, qualified_name, script_name, description, module_id, process_id, role_id)
SELECT
  'FIN.P2P.AP.0001',
  'FIN.P2P.AP.0001',
  'Create Standard Supplier Invoice',
  'Validates creation and submission of a standard supplier invoice for payment processing.',
  (SELECT id FROM modules WHERE name = 'Accounts Payable (AP)'),
  (SELECT id FROM processes WHERE name = 'Procure to Pay (P2P)'),
  (SELECT id FROM roles WHERE name = 'Accounts Payable Specialist')
ON CONFLICT DO NOTHING;
