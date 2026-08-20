-- V008: Indexes for enterprise paginated list APIs
-- Supports efficient filtering and sorting on date ranges and status fields

-- Test Runs: date range filtering and sorting
CREATE INDEX IF NOT EXISTS idx_tr_creation_date ON test_runs (creation_date DESC);
CREATE INDEX IF NOT EXISTS idx_tr_actual_start ON test_runs (actual_start_time DESC) WHERE actual_start_time IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_tr_actual_end ON test_runs (actual_end_time DESC) WHERE actual_end_time IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_tr_active_created ON test_runs (creation_date DESC) WHERE is_deleted = FALSE;

-- Test Run Scripts: dependency status filter, execution order composite
CREATE INDEX IF NOT EXISTS idx_trs_dependency_status ON test_run_scripts (dependency_status_code);
CREATE INDEX IF NOT EXISTS idx_trs_execution_order ON test_run_scripts (test_run_id, execution_order);

-- Test Run Script Step Results: pagination and filtering
CREATE INDEX IF NOT EXISTS idx_trsrs_script_step ON test_run_script_step_results (test_run_script_id, step_no);
CREATE INDEX IF NOT EXISTS idx_trsrs_status ON test_run_script_step_results (execution_status_code);
CREATE INDEX IF NOT EXISTS idx_trsrs_attempt ON test_run_script_step_results (test_run_script_id, attempt_no);

-- Master Steps: pagination support
CREATE INDEX IF NOT EXISTS idx_ms_script_step ON master_steps (script_id, step_no);
CREATE INDEX IF NOT EXISTS idx_ms_action ON master_steps (action) WHERE is_active = TRUE;
