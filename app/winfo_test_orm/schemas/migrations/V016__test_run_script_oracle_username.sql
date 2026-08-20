-- V016 – Per-script Oracle execution user
-- Lets each Test Run Script select its own Oracle login (e.g. FIN_IMPL, HR_IMPL,
-- SCM_IMPL) instead of always using the test run's shared configuration_id
-- credentials. Only the username is stored — the password is never persisted
-- here; it is resolved at execution time from OCI Vault
-- (backend/recording-service/app/utils/keyvault.py).

ALTER TABLE wt2dev.test_run_scripts
    ADD COLUMN IF NOT EXISTS oracle_username VARCHAR(100) NULL;

COMMENT ON COLUMN wt2dev.test_run_scripts.oracle_username IS
    'Oracle ERP username used to execute this specific script. Password is resolved dynamically from OCI Vault at run time and must never be stored here or elsewhere.';
