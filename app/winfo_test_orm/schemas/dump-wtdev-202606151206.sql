--
-- PostgreSQL database dump
--

\restrict Dhqcp1KyJLRmt9d4gH7wKMubS3hfvUhyEPpkrcJXavrdMaj73dg7ddcN75iduZ9

-- Dumped from database version 16.8
-- Dumped by pg_dump version 18.2

-- Started on 2026-06-15 12:06:22

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 7 (class 2615 OID 16676)
-- Name: wt2dev; Type: SCHEMA; Schema: -; Owner: wtadmin
--

CREATE SCHEMA wt2dev;


ALTER SCHEMA wt2dev OWNER TO wtadmin;

--
-- TOC entry 251 (class 1255 OID 20434)
-- Name: fn_build_test_script_search_document(); Type: FUNCTION; Schema: wt2dev; Owner: wtuser_dev
--

CREATE FUNCTION wt2dev.fn_build_test_script_search_document() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN

    NEW.search_document :=
        trim(
            concat_ws(
                ' ',

                COALESCE(NEW.qualified_name,''),

                COALESCE(NEW.script_name,''),

                COALESCE(NEW.objective,''),

                COALESCE(NEW.agent_intent_name,''),

                COALESCE(NEW.script_description,'')
            )
        );

    NEW.search_vector :=
        to_tsvector(
            'english',
            COALESCE(NEW.search_document,'')
        );

    RETURN NEW;

END;
$$;


ALTER FUNCTION wt2dev.fn_build_test_script_search_document() OWNER TO wtuser_dev;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 248 (class 1259 OID 20542)
-- Name: account; Type: TABLE; Schema: wt2dev; Owner: wtuser_dev
--

CREATE TABLE wt2dev.account (
    account_id uuid DEFAULT gen_random_uuid() NOT NULL,
    name character varying(150) NOT NULL,
    description character varying(150) NOT NULL,
    start_date timestamp with time zone NOT NULL,
    end_date timestamp with time zone NOT NULL,
    user_limit integer NOT NULL,
    scripts_created_limit integer NOT NULL,
    scripts_runs_limit integer NOT NULL,
    is_deleted boolean DEFAULT false NOT NULL,
    created_on timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by uuid,
    updated_on timestamp with time zone,
    updated_by uuid,
    row_version integer DEFAULT 1 NOT NULL,
    client_spoc uuid
);


ALTER TABLE wt2dev.account OWNER TO wtuser_dev;

--
-- TOC entry 249 (class 1259 OID 20551)
-- Name: account_history; Type: TABLE; Schema: wt2dev; Owner: wtuser_dev
--

CREATE TABLE wt2dev.account_history (
    account_history_id uuid DEFAULT gen_random_uuid() NOT NULL,
    operation character varying(10) NOT NULL,
    changed_on timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    changed_by uuid,
    account_id uuid NOT NULL,
    name character varying(150) NOT NULL,
    description character varying(150) NOT NULL,
    start_date timestamp with time zone NOT NULL,
    end_date timestamp with time zone NOT NULL,
    user_limit integer NOT NULL,
    scripts_created_limit integer NOT NULL,
    scripts_runs_limit integer NOT NULL,
    is_deleted boolean NOT NULL,
    created_on timestamp with time zone NOT NULL,
    created_by uuid,
    updated_on timestamp with time zone,
    updated_by uuid,
    row_version integer NOT NULL,
    client_spoc uuid
);


ALTER TABLE wt2dev.account_history OWNER TO wtuser_dev;

--
-- TOC entry 225 (class 1259 OID 16811)
-- Name: acl_resource_role_details; Type: TABLE; Schema: wt2dev; Owner: wtuser_dev
--

CREATE TABLE wt2dev.acl_resource_role_details (
    acl_resource_role_details_id uuid DEFAULT gen_random_uuid() NOT NULL,
    acl_resource_id uuid NOT NULL,
    acl_value jsonb DEFAULT '[]'::jsonb,
    is_deleted boolean DEFAULT false NOT NULL,
    created_on timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by uuid,
    updated_on timestamp with time zone,
    updated_by uuid,
    row_version integer DEFAULT 1 NOT NULL
);


ALTER TABLE wt2dev.acl_resource_role_details OWNER TO wtuser_dev;

--
-- TOC entry 226 (class 1259 OID 16827)
-- Name: acl_resource_role_details_history; Type: TABLE; Schema: wt2dev; Owner: wtuser_dev
--

CREATE TABLE wt2dev.acl_resource_role_details_history (
    acl_resource_role_details_history_id uuid DEFAULT gen_random_uuid() NOT NULL,
    acl_resource_role_id uuid NOT NULL,
    acl_resource_id uuid NOT NULL,
    acl_value jsonb DEFAULT '[]'::jsonb,
    operation character varying(10) NOT NULL,
    is_deleted boolean,
    created_on timestamp with time zone,
    created_by uuid,
    updated_on timestamp with time zone,
    updated_by uuid,
    changed_on timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    changed_by uuid
);


ALTER TABLE wt2dev.acl_resource_role_details_history OWNER TO wtuser_dev;

--
-- TOC entry 224 (class 1259 OID 16792)
-- Name: acl_role_grant_policy; Type: TABLE; Schema: wt2dev; Owner: wtuser_dev
--

CREATE TABLE wt2dev.acl_role_grant_policy (
    acl_role_grant_policy_id uuid DEFAULT gen_random_uuid() NOT NULL,
    acl_grant_role_id uuid NOT NULL,
    acl_target_role_id uuid NOT NULL,
    is_deleted boolean DEFAULT false NOT NULL,
    created_on timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by uuid,
    updated_on timestamp with time zone,
    updated_by uuid,
    row_version integer DEFAULT 1 NOT NULL
);


ALTER TABLE wt2dev.acl_role_grant_policy OWNER TO wtuser_dev;

--
-- TOC entry 223 (class 1259 OID 16781)
-- Name: acl_role_master; Type: TABLE; Schema: wt2dev; Owner: wtuser_dev
--

CREATE TABLE wt2dev.acl_role_master (
    acl_role_id uuid DEFAULT gen_random_uuid() NOT NULL,
    acl_role_name character varying(100) NOT NULL,
    is_deleted boolean DEFAULT false NOT NULL,
    created_on timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by uuid,
    updated_on timestamp with time zone,
    updated_by uuid,
    row_version integer DEFAULT 1 NOT NULL,
    CONSTRAINT chk_acl_role_name_upper CHECK (((acl_role_name)::text = upper((acl_role_name)::text)))
);


ALTER TABLE wt2dev.acl_role_master OWNER TO wtuser_dev;

--
-- TOC entry 234 (class 1259 OID 20221)
-- Name: application_releases; Type: TABLE; Schema: wt2dev; Owner: wtuser_dev
--

CREATE TABLE wt2dev.application_releases (
    application_release_id uuid DEFAULT gen_random_uuid() NOT NULL,
    application_id uuid NOT NULL,
    release_code character varying(50) NOT NULL,
    release_name character varying(255) NOT NULL,
    release_start_date date,
    release_end_date date,
    release_notes text,
    status_code character varying(30) NOT NULL,
    version_no integer DEFAULT 1 NOT NULL,
    is_deleted boolean DEFAULT false NOT NULL,
    deleted_date timestamp with time zone,
    deleted_by uuid,
    creation_date timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by uuid NOT NULL,
    last_update_date timestamp with time zone,
    last_updated_by uuid
);


ALTER TABLE wt2dev.application_releases OWNER TO wtuser_dev;

--
-- TOC entry 246 (class 1259 OID 20464)
-- Name: application_users; Type: TABLE; Schema: wt2dev; Owner: wtuser_dev
--

CREATE TABLE wt2dev.application_users (
    application_users_id uuid DEFAULT gen_random_uuid() NOT NULL,
    email character varying(150) NOT NULL,
    first_name character varying(150) NOT NULL,
    last_name character varying(150) NOT NULL,
    source character varying(150),
    is_deleted boolean DEFAULT false NOT NULL,
    created_on timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by uuid,
    updated_on timestamp with time zone,
    updated_by uuid,
    row_version integer DEFAULT 1 NOT NULL,
    password_hash character varying(255) NOT NULL
);


ALTER TABLE wt2dev.application_users OWNER TO wtuser_dev;

--
-- TOC entry 230 (class 1259 OID 20130)
-- Name: applications; Type: TABLE; Schema: wt2dev; Owner: wtuser_dev
--

CREATE TABLE wt2dev.applications (
    application_id uuid DEFAULT gen_random_uuid() NOT NULL,
    application_code character varying(50) NOT NULL,
    application_name character varying(255) NOT NULL,
    application_description text,
    vendor_name character varying(255),
    status_code character varying(30) NOT NULL,
    version_no integer DEFAULT 1 NOT NULL,
    is_deleted boolean DEFAULT false NOT NULL,
    deleted_date timestamp with time zone,
    deleted_by uuid,
    creation_date timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by uuid NOT NULL,
    last_update_date timestamp with time zone,
    last_updated_by uuid
);


ALTER TABLE wt2dev.applications OWNER TO wtuser_dev;

--
-- TOC entry 237 (class 1259 OID 20280)
-- Name: labels; Type: TABLE; Schema: wt2dev; Owner: wtuser_dev
--

CREATE TABLE wt2dev.labels (
    label_id uuid DEFAULT gen_random_uuid() NOT NULL,
    label_name character varying(100) NOT NULL,
    status_code character varying(30) NOT NULL,
    version_no integer DEFAULT 1 NOT NULL,
    is_deleted boolean DEFAULT false NOT NULL,
    deleted_date timestamp with time zone,
    deleted_by uuid,
    creation_date timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by uuid NOT NULL,
    last_update_date timestamp with time zone,
    last_updated_by uuid
);


ALTER TABLE wt2dev.labels OWNER TO wtuser_dev;

--
-- TOC entry 233 (class 1259 OID 20196)
-- Name: modules; Type: TABLE; Schema: wt2dev; Owner: wtuser_dev
--

CREATE TABLE wt2dev.modules (
    module_id uuid DEFAULT gen_random_uuid() NOT NULL,
    process_area_id uuid NOT NULL,
    module_code character varying(50) NOT NULL,
    module_name character varying(255) NOT NULL,
    module_description text,
    status_code character varying(30) NOT NULL,
    display_sequence integer DEFAULT 0,
    version_no integer DEFAULT 1 NOT NULL,
    is_deleted boolean DEFAULT false NOT NULL,
    deleted_date timestamp with time zone,
    deleted_by uuid,
    creation_date timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by uuid NOT NULL,
    last_update_date timestamp with time zone,
    last_updated_by uuid
);


ALTER TABLE wt2dev.modules OWNER TO wtuser_dev;

--
-- TOC entry 232 (class 1259 OID 20172)
-- Name: process_areas; Type: TABLE; Schema: wt2dev; Owner: wtuser_dev
--

CREATE TABLE wt2dev.process_areas (
    process_area_id uuid DEFAULT gen_random_uuid() NOT NULL,
    stream_id uuid NOT NULL,
    process_area_code character varying(50) NOT NULL,
    process_area_name character varying(255) NOT NULL,
    process_area_description text,
    status_code character varying(30) NOT NULL,
    display_sequence integer DEFAULT 0,
    version_no integer DEFAULT 1 NOT NULL,
    is_deleted boolean DEFAULT false NOT NULL,
    deleted_date timestamp with time zone,
    deleted_by uuid,
    creation_date timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by uuid NOT NULL,
    last_update_date timestamp with time zone,
    last_updated_by uuid
);


ALTER TABLE wt2dev.process_areas OWNER TO wtuser_dev;

--
-- TOC entry 236 (class 1259 OID 20262)
-- Name: processes; Type: TABLE; Schema: wt2dev; Owner: wtuser_dev
--

CREATE TABLE wt2dev.processes (
    process_id uuid DEFAULT gen_random_uuid() NOT NULL,
    process_code character varying(50) NOT NULL,
    process_name character varying(255) NOT NULL,
    process_description text,
    status_code character varying(30) NOT NULL,
    version_no integer DEFAULT 1 NOT NULL,
    is_deleted boolean DEFAULT false NOT NULL,
    deleted_date timestamp with time zone,
    deleted_by uuid,
    creation_date timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by uuid NOT NULL,
    last_update_date timestamp with time zone,
    last_updated_by uuid
);


ALTER TABLE wt2dev.processes OWNER TO wtuser_dev;

--
-- TOC entry 245 (class 1259 OID 20451)
-- Name: resource_additional_values; Type: TABLE; Schema: wt2dev; Owner: wtuser_dev
--

CREATE TABLE wt2dev.resource_additional_values (
    resource_id uuid NOT NULL,
    first_name character varying(150) NOT NULL,
    last_name character varying(150) NOT NULL,
    start_date timestamp with time zone NOT NULL,
    end_date timestamp with time zone NOT NULL,
    is_deleted boolean DEFAULT false NOT NULL,
    created_on timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by uuid,
    updated_on timestamp with time zone,
    updated_by uuid,
    row_version integer DEFAULT 1 NOT NULL
);


ALTER TABLE wt2dev.resource_additional_values OWNER TO wtuser_dev;

--
-- TOC entry 222 (class 1259 OID 16754)
-- Name: resource_master; Type: TABLE; Schema: wt2dev; Owner: wtuser_dev
--

CREATE TABLE wt2dev.resource_master (
    resource_id uuid DEFAULT gen_random_uuid() NOT NULL,
    employee_code character varying(50) NOT NULL,
    email_address character varying(256) NOT NULL,
    profile_photo_url character varying(512),
    is_deleted boolean DEFAULT false NOT NULL,
    created_on timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by uuid,
    updated_on timestamp with time zone,
    updated_by uuid,
    row_version integer DEFAULT 1 NOT NULL,
    CONSTRAINT chk_email_lower CHECK (((email_address)::text = lower((email_address)::text))),
    CONSTRAINT chk_employee_code_upper CHECK (((employee_code)::text = upper((employee_code)::text)))
);


ALTER TABLE wt2dev.resource_master OWNER TO wtuser_dev;

--
-- TOC entry 235 (class 1259 OID 20244)
-- Name: roles; Type: TABLE; Schema: wt2dev; Owner: wtuser_dev
--

CREATE TABLE wt2dev.roles (
    role_id uuid DEFAULT gen_random_uuid() NOT NULL,
    role_code character varying(50) NOT NULL,
    role_name character varying(255) NOT NULL,
    role_description text,
    status_code character varying(30) NOT NULL,
    version_no integer DEFAULT 1 NOT NULL,
    is_deleted boolean DEFAULT false NOT NULL,
    deleted_date timestamp with time zone,
    deleted_by uuid,
    creation_date timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by uuid NOT NULL,
    last_update_date timestamp with time zone,
    last_updated_by uuid
);


ALTER TABLE wt2dev.roles OWNER TO wtuser_dev;

--
-- TOC entry 229 (class 1259 OID 20125)
-- Name: runtime_type_master; Type: TABLE; Schema: wt2dev; Owner: wtuser_dev
--

CREATE TABLE wt2dev.runtime_type_master (
    runtime_type_code character varying(30) NOT NULL,
    runtime_type_name character varying(100) NOT NULL
);


ALTER TABLE wt2dev.runtime_type_master OWNER TO wtuser_dev;

--
-- TOC entry 228 (class 1259 OID 20120)
-- Name: script_type_master; Type: TABLE; Schema: wt2dev; Owner: wtuser_dev
--

CREATE TABLE wt2dev.script_type_master (
    script_type_code character varying(30) NOT NULL,
    script_type_name character varying(100) NOT NULL
);


ALTER TABLE wt2dev.script_type_master OWNER TO wtuser_dev;

--
-- TOC entry 227 (class 1259 OID 20115)
-- Name: status_master; Type: TABLE; Schema: wt2dev; Owner: wtuser_dev
--

CREATE TABLE wt2dev.status_master (
    status_code character varying(30) NOT NULL,
    status_name character varying(100) NOT NULL
);


ALTER TABLE wt2dev.status_master OWNER TO wtuser_dev;

--
-- TOC entry 231 (class 1259 OID 20148)
-- Name: streams; Type: TABLE; Schema: wt2dev; Owner: wtuser_dev
--

CREATE TABLE wt2dev.streams (
    stream_id uuid DEFAULT gen_random_uuid() NOT NULL,
    application_id uuid NOT NULL,
    stream_code character varying(50) NOT NULL,
    stream_name character varying(255) NOT NULL,
    stream_description text,
    status_code character varying(30) NOT NULL,
    display_sequence integer DEFAULT 0,
    version_no integer DEFAULT 1 NOT NULL,
    is_deleted boolean DEFAULT false NOT NULL,
    deleted_date timestamp with time zone,
    deleted_by uuid,
    creation_date timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by uuid NOT NULL,
    last_update_date timestamp with time zone,
    last_updated_by uuid
);


ALTER TABLE wt2dev.streams OWNER TO wtuser_dev;

--
-- TOC entry 239 (class 1259 OID 20332)
-- Name: test_script_dependencies; Type: TABLE; Schema: wt2dev; Owner: wtuser_dev
--

CREATE TABLE wt2dev.test_script_dependencies (
    test_script_dependency_id uuid DEFAULT gen_random_uuid() NOT NULL,
    test_script_id uuid NOT NULL,
    depends_on_test_script_id uuid NOT NULL,
    creation_date timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by uuid NOT NULL,
    CONSTRAINT test_script_dependencies_check CHECK ((test_script_id <> depends_on_test_script_id))
);


ALTER TABLE wt2dev.test_script_dependencies OWNER TO wtuser_dev;

--
-- TOC entry 243 (class 1259 OID 20409)
-- Name: test_script_labels; Type: TABLE; Schema: wt2dev; Owner: wtuser_dev
--

CREATE TABLE wt2dev.test_script_labels (
    test_script_label_id uuid DEFAULT gen_random_uuid() NOT NULL,
    test_script_id uuid NOT NULL,
    label_id uuid NOT NULL,
    creation_date timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by uuid NOT NULL
);


ALTER TABLE wt2dev.test_script_labels OWNER TO wtuser_dev;

--
-- TOC entry 242 (class 1259 OID 20390)
-- Name: test_script_processes; Type: TABLE; Schema: wt2dev; Owner: wtuser_dev
--

CREATE TABLE wt2dev.test_script_processes (
    test_script_process_id uuid DEFAULT gen_random_uuid() NOT NULL,
    test_script_id uuid NOT NULL,
    process_id uuid NOT NULL,
    creation_date timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by uuid NOT NULL
);


ALTER TABLE wt2dev.test_script_processes OWNER TO wtuser_dev;

--
-- TOC entry 240 (class 1259 OID 20352)
-- Name: test_script_releases; Type: TABLE; Schema: wt2dev; Owner: wtuser_dev
--

CREATE TABLE wt2dev.test_script_releases (
    test_script_release_id uuid DEFAULT gen_random_uuid() NOT NULL,
    test_script_id uuid NOT NULL,
    application_release_id uuid NOT NULL,
    creation_date timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by uuid NOT NULL
);


ALTER TABLE wt2dev.test_script_releases OWNER TO wtuser_dev;

--
-- TOC entry 241 (class 1259 OID 20371)
-- Name: test_script_roles; Type: TABLE; Schema: wt2dev; Owner: wtuser_dev
--

CREATE TABLE wt2dev.test_script_roles (
    test_script_role_id uuid DEFAULT gen_random_uuid() NOT NULL,
    test_script_id uuid NOT NULL,
    role_id uuid NOT NULL,
    creation_date timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by uuid NOT NULL
);


ALTER TABLE wt2dev.test_script_roles OWNER TO wtuser_dev;

--
-- TOC entry 238 (class 1259 OID 20296)
-- Name: test_scripts; Type: TABLE; Schema: wt2dev; Owner: wtuser_dev
--

CREATE TABLE wt2dev.test_scripts (
    test_script_id uuid DEFAULT gen_random_uuid() NOT NULL,
    module_id uuid NOT NULL,
    test_case_number character varying(50) NOT NULL,
    qualified_name character varying(1000) NOT NULL,
    script_name character varying(500) NOT NULL,
    script_description text,
    objective text,
    agent_intent_name character varying(500),
    search_document text,
    search_vector tsvector,
    script_type_code character varying(30) NOT NULL,
    runtime_type_code character varying(30) NOT NULL,
    estimated_duration_seconds integer,
    display_sequence integer DEFAULT 0,
    status_code character varying(30) NOT NULL,
    version_no integer DEFAULT 1 NOT NULL,
    is_deleted boolean DEFAULT false NOT NULL,
    deleted_date timestamp with time zone,
    deleted_by uuid,
    creation_date timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by uuid NOT NULL,
    last_update_date timestamp with time zone,
    last_updated_by uuid
);


ALTER TABLE wt2dev.test_scripts OWNER TO wtuser_dev;

--
-- TOC entry 247 (class 1259 OID 20507)
-- Name: workspace; Type: TABLE; Schema: wt2dev; Owner: wtuser_dev
--

CREATE TABLE wt2dev.workspace (
    workspace_id uuid DEFAULT gen_random_uuid() NOT NULL,
    name character varying(150) NOT NULL,
    description character varying(150) NOT NULL,
    application_release_id uuid NOT NULL,
    process_area_id uuid NOT NULL,
    workspace_configurations_id uuid,
    access_window_from timestamp with time zone NOT NULL,
    access_window_to timestamp with time zone NOT NULL,
    application_users jsonb DEFAULT '[]'::jsonb,
    is_deleted boolean DEFAULT false NOT NULL,
    created_on timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by uuid,
    updated_on timestamp with time zone,
    updated_by uuid,
    row_version integer DEFAULT 1 NOT NULL
);


ALTER TABLE wt2dev.workspace OWNER TO wtuser_dev;

--
-- TOC entry 244 (class 1259 OID 20439)
-- Name: workspace_configurations; Type: TABLE; Schema: wt2dev; Owner: wtuser_dev
--

CREATE TABLE wt2dev.workspace_configurations (
    workspace_configurations_id uuid DEFAULT gen_random_uuid() NOT NULL,
    configuration character varying(150) NOT NULL,
    smtp_form character varying(150) NOT NULL,
    parameters jsonb DEFAULT '[]'::jsonb,
    is_deleted boolean DEFAULT false NOT NULL,
    created_on timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by uuid,
    updated_on timestamp with time zone,
    updated_by uuid,
    row_version integer DEFAULT 1 NOT NULL
);


ALTER TABLE wt2dev.workspace_configurations OWNER TO wtuser_dev;

--
-- TOC entry 250 (class 1259 OID 20602)
-- Name: workspace_resource; Type: TABLE; Schema: wt2dev; Owner: wtuser_dev
--

CREATE TABLE wt2dev.workspace_resource (
    workspace_resource_id uuid DEFAULT gen_random_uuid() NOT NULL,
    resource_id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    is_deleted boolean DEFAULT false NOT NULL,
    created_on timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by uuid,
    updated_on timestamp with time zone,
    updated_by uuid,
    row_version integer DEFAULT 1 NOT NULL
);


ALTER TABLE wt2dev.workspace_resource OWNER TO wtuser_dev;

--
-- TOC entry 4676 (class 0 OID 20542)
-- Dependencies: 248
-- Data for Name: account; Type: TABLE DATA; Schema: wt2dev; Owner: wtuser_dev
--

COPY wt2dev.account (account_id, name, description, start_date, end_date, user_limit, scripts_created_limit, scripts_runs_limit, is_deleted, created_on, created_by, updated_on, updated_by, row_version, client_spoc) FROM stdin;
4cb0e574-fe23-42c9-8602-9184d7f7e8c6	Testing	Testing application	2026-06-10 13:28:52.384+00	2026-06-13 13:28:52.384+00	20	200	10	f	2026-06-10 13:31:36.435248+00	37f2450c-f3da-468d-82d7-9fc07aa1f17d	2026-06-10 13:33:14.874423+00	37f2450c-f3da-468d-82d7-9fc07aa1f17d	2	f0d8e25f-a1bc-46e0-940d-a4d5222b3ad1
\.


--
-- TOC entry 4677 (class 0 OID 20551)
-- Dependencies: 249
-- Data for Name: account_history; Type: TABLE DATA; Schema: wt2dev; Owner: wtuser_dev
--

COPY wt2dev.account_history (account_history_id, operation, changed_on, changed_by, account_id, name, description, start_date, end_date, user_limit, scripts_created_limit, scripts_runs_limit, is_deleted, created_on, created_by, updated_on, updated_by, row_version, client_spoc) FROM stdin;
e07dd273-83dc-4344-8da8-25ce0d9d0baa	INSERT	2026-06-10 13:31:38.864764+00	37f2450c-f3da-468d-82d7-9fc07aa1f17d	4cb0e574-fe23-42c9-8602-9184d7f7e8c6	Testingv	Testing application	2026-06-10 13:28:52.384+00	2026-06-13 13:28:52.384+00	20	200	10	f	2026-06-10 13:31:36.435248+00	37f2450c-f3da-468d-82d7-9fc07aa1f17d	\N	\N	1	f0d8e25f-a1bc-46e0-940d-a4d5222b3ad1
65025dbe-cfb7-4dcb-abf1-18f2090cd0c6	UPDATE	2026-06-10 13:33:15.695097+00	37f2450c-f3da-468d-82d7-9fc07aa1f17d	4cb0e574-fe23-42c9-8602-9184d7f7e8c6	Testing	Testing application	2026-06-10 13:28:52.384+00	2026-06-13 13:28:52.384+00	20	200	10	f	2026-06-10 13:31:36.435248+00	37f2450c-f3da-468d-82d7-9fc07aa1f17d	2026-06-10 13:33:14.874423+00	37f2450c-f3da-468d-82d7-9fc07aa1f17d	2	f0d8e25f-a1bc-46e0-940d-a4d5222b3ad1
\.


--
-- TOC entry 4653 (class 0 OID 16811)
-- Dependencies: 225
-- Data for Name: acl_resource_role_details; Type: TABLE DATA; Schema: wt2dev; Owner: wtuser_dev
--

COPY wt2dev.acl_resource_role_details (acl_resource_role_details_id, acl_resource_id, acl_value, is_deleted, created_on, created_by, updated_on, updated_by, row_version) FROM stdin;
\.


--
-- TOC entry 4654 (class 0 OID 16827)
-- Dependencies: 226
-- Data for Name: acl_resource_role_details_history; Type: TABLE DATA; Schema: wt2dev; Owner: wtuser_dev
--

COPY wt2dev.acl_resource_role_details_history (acl_resource_role_details_history_id, acl_resource_role_id, acl_resource_id, acl_value, operation, is_deleted, created_on, created_by, updated_on, updated_by, changed_on, changed_by) FROM stdin;
\.


--
-- TOC entry 4652 (class 0 OID 16792)
-- Dependencies: 224
-- Data for Name: acl_role_grant_policy; Type: TABLE DATA; Schema: wt2dev; Owner: wtuser_dev
--

COPY wt2dev.acl_role_grant_policy (acl_role_grant_policy_id, acl_grant_role_id, acl_target_role_id, is_deleted, created_on, created_by, updated_on, updated_by, row_version) FROM stdin;
\.


--
-- TOC entry 4651 (class 0 OID 16781)
-- Dependencies: 223
-- Data for Name: acl_role_master; Type: TABLE DATA; Schema: wt2dev; Owner: wtuser_dev
--

COPY wt2dev.acl_role_master (acl_role_id, acl_role_name, is_deleted, created_on, created_by, updated_on, updated_by, row_version) FROM stdin;
\.


--
-- TOC entry 4662 (class 0 OID 20221)
-- Dependencies: 234
-- Data for Name: application_releases; Type: TABLE DATA; Schema: wt2dev; Owner: wtuser_dev
--

COPY wt2dev.application_releases (application_release_id, application_id, release_code, release_name, release_start_date, release_end_date, release_notes, status_code, version_no, is_deleted, deleted_date, deleted_by, creation_date, created_by, last_update_date, last_updated_by) FROM stdin;
651463ee-4266-49d3-a090-9f9a683337c6	b922bdb0-c88c-4a16-bcd1-49af58b1f007	R13	R13 26B	2026-06-10	2026-06-20	test	PUBLISHED	1	f	\N	\N	2026-06-10 12:29:01.36267+00	37f2450c-f3da-468d-82d7-9fc07aa1f17d	\N	\N
a616351b-ad67-40c7-a9fd-b2e282a4db16	b922bdb0-c88c-4a16-bcd1-49af58b1f007	R14	R15 26B	2026-06-10	2026-06-10	test	PUBLISHED	2	f	\N	\N	2026-06-10 12:30:41.156946+00	37f2450c-f3da-468d-82d7-9fc07aa1f17d	2026-06-10 12:32:57.194135+00	37f2450c-f3da-468d-82d7-9fc07aa1f17d
\.


--
-- TOC entry 4674 (class 0 OID 20464)
-- Dependencies: 246
-- Data for Name: application_users; Type: TABLE DATA; Schema: wt2dev; Owner: wtuser_dev
--

COPY wt2dev.application_users (application_users_id, email, first_name, last_name, source, is_deleted, created_on, created_by, updated_on, updated_by, row_version, password_hash) FROM stdin;
2e02cb8a-7424-46f8-b9f2-2ca899bcd115	Test1@winfosolutions.com	Test1	1Test	Prod	f	2026-06-10 12:34:50.273318+00	37f2450c-f3da-468d-82d7-9fc07aa1f17d	\N	\N	1	$2b$12$TjhN..AO0sYGXd1Cnw4FuetPnCTJIBlu5TeBNmKJsRLRYg2k.YtxG
68a8b435-cd31-47b2-a263-f91abfcf8af3	Test2@winfosolutions.com	Test2	testing2	Prod	f	2026-06-10 12:35:20.341352+00	37f2450c-f3da-468d-82d7-9fc07aa1f17d	2026-06-10 12:36:35.056101+00	37f2450c-f3da-468d-82d7-9fc07aa1f17d	2	$2b$12$bG5sC69hRjN4o78aSzgLKeKSuHrBbqizqpD642Eyyjw1i7DGdeSIm
\.


--
-- TOC entry 4658 (class 0 OID 20130)
-- Dependencies: 230
-- Data for Name: applications; Type: TABLE DATA; Schema: wt2dev; Owner: wtuser_dev
--

COPY wt2dev.applications (application_id, application_code, application_name, application_description, vendor_name, status_code, version_no, is_deleted, deleted_date, deleted_by, creation_date, created_by, last_update_date, last_updated_by) FROM stdin;
b922bdb0-c88c-4a16-bcd1-49af58b1f007	ORACLE_FUSION	Oracle Fusion Cloud Applications	Oracle Fusion ERP, SCM, HCM, CX and related Oracle Cloud Applications.	Oracle Corporation	PUBLISHED	1	f	\N	\N	2026-06-09 11:19:46.671558+00	00000000-0000-0000-0000-000000000000	\N	\N
\.


--
-- TOC entry 4665 (class 0 OID 20280)
-- Dependencies: 237
-- Data for Name: labels; Type: TABLE DATA; Schema: wt2dev; Owner: wtuser_dev
--

COPY wt2dev.labels (label_id, label_name, status_code, version_no, is_deleted, deleted_date, deleted_by, creation_date, created_by, last_update_date, last_updated_by) FROM stdin;
\.


--
-- TOC entry 4661 (class 0 OID 20196)
-- Dependencies: 233
-- Data for Name: modules; Type: TABLE DATA; Schema: wt2dev; Owner: wtuser_dev
--

COPY wt2dev.modules (module_id, process_area_id, module_code, module_name, module_description, status_code, display_sequence, version_no, is_deleted, deleted_date, deleted_by, creation_date, created_by, last_update_date, last_updated_by) FROM stdin;
\.


--
-- TOC entry 4660 (class 0 OID 20172)
-- Dependencies: 232
-- Data for Name: process_areas; Type: TABLE DATA; Schema: wt2dev; Owner: wtuser_dev
--

COPY wt2dev.process_areas (process_area_id, stream_id, process_area_code, process_area_name, process_area_description, status_code, display_sequence, version_no, is_deleted, deleted_date, deleted_by, creation_date, created_by, last_update_date, last_updated_by) FROM stdin;
4a41ea5e-4b45-4952-922b-359a2a1217b0	f4bf4b86-9275-4e40-9af7-f3a246c836c2	HR	Human resources	human resources	PUBLISHED	1	1	f	\N	\N	2026-06-10 11:34:30.686466+00	37f2450c-f3da-468d-82d7-9fc07aa1f17d	\N	\N
42768991-026b-4d89-8db8-fe148accf031	f4bf4b86-9275-4e40-9af7-f3a246c836c2	FM	Finance	Finance	PUBLISHED	2	2	f	\N	\N	2026-06-10 11:35:08.266657+00	37f2450c-f3da-468d-82d7-9fc07aa1f17d	2026-06-10 12:25:06.033064+00	37f2450c-f3da-468d-82d7-9fc07aa1f17d
\.


--
-- TOC entry 4664 (class 0 OID 20262)
-- Dependencies: 236
-- Data for Name: processes; Type: TABLE DATA; Schema: wt2dev; Owner: wtuser_dev
--

COPY wt2dev.processes (process_id, process_code, process_name, process_description, status_code, version_no, is_deleted, deleted_date, deleted_by, creation_date, created_by, last_update_date, last_updated_by) FROM stdin;
\.


--
-- TOC entry 4673 (class 0 OID 20451)
-- Dependencies: 245
-- Data for Name: resource_additional_values; Type: TABLE DATA; Schema: wt2dev; Owner: wtuser_dev
--

COPY wt2dev.resource_additional_values (resource_id, first_name, last_name, start_date, end_date, is_deleted, created_on, created_by, updated_on, updated_by, row_version) FROM stdin;
faa6f927-aeaf-465b-a135-3df4dcdc93b0	test4	test4	2026-06-10 12:37:15.828+00	2026-06-20 12:37:15.828+00	f	2026-06-10 12:39:40.853664+00	37f2450c-f3da-468d-82d7-9fc07aa1f17d	\N	\N	1
f0d8e25f-a1bc-46e0-940d-a4d5222b3ad1	Reddeppa	test3	2026-06-10 12:37:15.828+00	2026-06-20 12:37:15.828+00	f	2026-06-10 12:39:23.485635+00	37f2450c-f3da-468d-82d7-9fc07aa1f17d	2026-06-10 12:42:40.896704+00	37f2450c-f3da-468d-82d7-9fc07aa1f17d	1
\.


--
-- TOC entry 4650 (class 0 OID 16754)
-- Dependencies: 222
-- Data for Name: resource_master; Type: TABLE DATA; Schema: wt2dev; Owner: wtuser_dev
--

COPY wt2dev.resource_master (resource_id, employee_code, email_address, profile_photo_url, is_deleted, created_on, created_by, updated_on, updated_by, row_version) FROM stdin;
faa6f927-aeaf-465b-a135-3df4dcdc93b0	EMP0003	test4@gmail.com	\N	f	2026-06-10 12:39:40.853664+00	37f2450c-f3da-468d-82d7-9fc07aa1f17d	\N	\N	1
f0d8e25f-a1bc-46e0-940d-a4d5222b3ad1	EMP0002	test3@gmail.com	\N	f	2026-06-10 12:39:23.485635+00	37f2450c-f3da-468d-82d7-9fc07aa1f17d	2026-06-10 12:42:40.549371+00	37f2450c-f3da-468d-82d7-9fc07aa1f17d	2
37f2450c-f3da-468d-82d7-9fc07aa1f17d	001	reddeppa.nallannagari@winfotest.com	\N	f	2026-05-26 08:44:18.328225+00	\N	2026-06-10 12:43:12.697698+00	37f2450c-f3da-468d-82d7-9fc07aa1f17d	4
\.


--
-- TOC entry 4663 (class 0 OID 20244)
-- Dependencies: 235
-- Data for Name: roles; Type: TABLE DATA; Schema: wt2dev; Owner: wtuser_dev
--

COPY wt2dev.roles (role_id, role_code, role_name, role_description, status_code, version_no, is_deleted, deleted_date, deleted_by, creation_date, created_by, last_update_date, last_updated_by) FROM stdin;
\.


--
-- TOC entry 4657 (class 0 OID 20125)
-- Dependencies: 229
-- Data for Name: runtime_type_master; Type: TABLE DATA; Schema: wt2dev; Owner: wtuser_dev
--

COPY wt2dev.runtime_type_master (runtime_type_code, runtime_type_name) FROM stdin;
ANY	Any
WEB	Web
WINDOWS	Windows
API	API
MOBILE	Mobile
\.


--
-- TOC entry 4656 (class 0 OID 20120)
-- Dependencies: 228
-- Data for Name: script_type_master; Type: TABLE DATA; Schema: wt2dev; Owner: wtuser_dev
--

COPY wt2dev.script_type_master (script_type_code, script_type_name) FROM stdin;
STANDARD	Standard
CUSTOMIZED	Customized
\.


--
-- TOC entry 4655 (class 0 OID 20115)
-- Dependencies: 227
-- Data for Name: status_master; Type: TABLE DATA; Schema: wt2dev; Owner: wtuser_dev
--

COPY wt2dev.status_master (status_code, status_name) FROM stdin;
DRAFT	Draft
PUBLISHED	Published
ARCHIVED	Archived
\.


--
-- TOC entry 4659 (class 0 OID 20148)
-- Dependencies: 231
-- Data for Name: streams; Type: TABLE DATA; Schema: wt2dev; Owner: wtuser_dev
--

COPY wt2dev.streams (stream_id, application_id, stream_code, stream_name, stream_description, status_code, display_sequence, version_no, is_deleted, deleted_date, deleted_by, creation_date, created_by, last_update_date, last_updated_by) FROM stdin;
f4bf4b86-9275-4e40-9af7-f3a246c836c2	b922bdb0-c88c-4a16-bcd1-49af58b1f007	PLM	Product Lifecycle Management	Product Development, Product Information Management and Innovation Management	PUBLISHED	0	1	f	\N	\N	2026-06-09 11:21:12.699857+00	00000000-0000-0000-0000-000000000000	\N	\N
51bb5172-6da5-4821-81ff-103730cbd2ad	b922bdb0-c88c-4a16-bcd1-49af58b1f007	WMS	Warehouse Management	Warehouse Operations, Picking, Packing and Inventory Movements	PUBLISHED	0	1	f	\N	\N	2026-06-09 11:21:12.699857+00	00000000-0000-0000-0000-000000000000	\N	\N
b4226648-5d28-4058-a59c-07ba1f236659	b922bdb0-c88c-4a16-bcd1-49af58b1f007	PRJ	Projects	Project Management and Project Execution	PUBLISHED	0	1	f	\N	\N	2026-06-09 11:21:12.699857+00	00000000-0000-0000-0000-000000000000	\N	\N
58c0c25f-7f46-4a9f-8e75-5200afc1f6b1	b922bdb0-c88c-4a16-bcd1-49af58b1f007	HCM	Human Capital Management	Core HR, Payroll, Talent Management and Workforce Management	PUBLISHED	0	1	f	\N	\N	2026-06-09 11:21:12.699857+00	00000000-0000-0000-0000-000000000000	\N	\N
6212d3f8-7427-4722-b710-3aac36d156ff	b922bdb0-c88c-4a16-bcd1-49af58b1f007	CPQ	Configure Price Quote	Quote Configuration, Pricing and Sales Automation	PUBLISHED	0	1	f	\N	\N	2026-06-09 11:21:12.699857+00	00000000-0000-0000-0000-000000000000	\N	\N
3bc19187-6781-47aa-a981-78c585cc7b44	b922bdb0-c88c-4a16-bcd1-49af58b1f007	SCM	Supply Chain Management	Inventory, Order Management and Supply Chain Execution	PUBLISHED	0	1	f	\N	\N	2026-06-09 11:21:12.699857+00	00000000-0000-0000-0000-000000000000	\N	\N
5853221b-acb7-4300-af53-3f2f7403cb46	b922bdb0-c88c-4a16-bcd1-49af58b1f007	SUB	Subscription Management	Subscription Lifecycle Management	PUBLISHED	0	1	f	\N	\N	2026-06-09 11:21:12.699857+00	00000000-0000-0000-0000-000000000000	\N	\N
e655ce22-64b9-4ced-949e-faab6b5bf241	b922bdb0-c88c-4a16-bcd1-49af58b1f007	LOG	Logistics	Shipping, Receiving and Logistics Operations	PUBLISHED	0	1	f	\N	\N	2026-06-09 11:21:12.699857+00	00000000-0000-0000-0000-000000000000	\N	\N
f16e41f8-c62f-45fe-a74f-099c939bd79b	b922bdb0-c88c-4a16-bcd1-49af58b1f007	PFM	Project Financial Management	Project Costing, Billing and Financial Control	PUBLISHED	0	1	f	\N	\N	2026-06-09 11:21:12.699857+00	00000000-0000-0000-0000-000000000000	\N	\N
3b0edc25-7f26-4b4f-88fc-e7ccb84365ce	b922bdb0-c88c-4a16-bcd1-49af58b1f007	PROC	Procurement	Supplier Management, Purchasing, Sourcing and Procurement Contracts	PUBLISHED	0	1	f	\N	\N	2026-06-09 11:21:12.699857+00	00000000-0000-0000-0000-000000000000	\N	\N
339b027a-bdb2-44b1-b7b5-62d3856ae821	b922bdb0-c88c-4a16-bcd1-49af58b1f007	EPM	Enterprise Performance Management	Planning, Budgeting, Consolidation and Financial Reporting	PUBLISHED	0	1	f	\N	\N	2026-06-09 11:21:12.699857+00	00000000-0000-0000-0000-000000000000	\N	\N
9409b87d-f558-4352-abac-5d4c4ec9c001	b922bdb0-c88c-4a16-bcd1-49af58b1f007	PPM	Project Portfolio Management	Project Portfolio Planning and Governance	PUBLISHED	0	1	f	\N	\N	2026-06-09 11:21:12.699857+00	00000000-0000-0000-0000-000000000000	\N	\N
a4904ae5-2f50-4ce9-8aaa-453dcec39ac9	b922bdb0-c88c-4a16-bcd1-49af58b1f007	EDM	Enterprise Data Management	Enterprise Master Data and Reference Data Management	PUBLISHED	0	1	f	\N	\N	2026-06-09 11:21:12.699857+00	00000000-0000-0000-0000-000000000000	\N	\N
405a3c3d-d1e7-4108-bc81-dfc40e018e33	b922bdb0-c88c-4a16-bcd1-49af58b1f007	REV	Revenue Management	Revenue Recognition and Revenue Accounting	PUBLISHED	0	1	f	\N	\N	2026-06-09 11:21:12.699857+00	00000000-0000-0000-0000-000000000000	\N	\N
b6f4b197-08d3-45d9-8227-740de8274410	b922bdb0-c88c-4a16-bcd1-49af58b1f007	OTM	Transportation Management	Transportation Planning, Freight Management and Logistics Optimization	PUBLISHED	0	1	f	\N	\N	2026-06-09 11:21:12.699857+00	00000000-0000-0000-0000-000000000000	\N	\N
a12b7be3-3dae-4991-8da2-74cf957d9077	b922bdb0-c88c-4a16-bcd1-49af58b1f007	FIN	Financials	General Ledger, Payables, Receivables, Assets, Cash Management and Accounting	PUBLISHED	0	1	f	\N	\N	2026-06-09 11:21:12.699857+00	00000000-0000-0000-0000-000000000000	\N	\N
52402cf1-078b-4ca8-89cb-63546c42e767	b922bdb0-c88c-4a16-bcd1-49af58b1f007	CX	Customer Experience	Sales, Marketing and Customer Service	PUBLISHED	0	1	f	\N	\N	2026-06-09 11:21:12.699857+00	00000000-0000-0000-0000-000000000000	\N	\N
a66038b5-d216-45be-b771-bebc0d18e639	b922bdb0-c88c-4a16-bcd1-49af58b1f007	MFG	Manufacturing	Discrete Manufacturing, Process Manufacturing and Production Execution	PUBLISHED	0	1	f	\N	\N	2026-06-09 11:21:12.699857+00	00000000-0000-0000-0000-000000000000	\N	\N
9cefca50-9a90-4652-bfa2-ed36e66ac692	b922bdb0-c88c-4a16-bcd1-49af58b1f007	RISK	Risk Management	Risk Identification, Assessment and Monitoring	PUBLISHED	0	1	f	\N	\N	2026-06-09 11:21:12.699857+00	00000000-0000-0000-0000-000000000000	\N	\N
848948b9-0451-48dc-af62-98de0cad9d4a	b922bdb0-c88c-4a16-bcd1-49af58b1f007	GRC	Governance Risk and Compliance	Controls, Audit Management and Compliance Monitoring	PUBLISHED	0	1	f	\N	\N	2026-06-09 11:21:12.699857+00	00000000-0000-0000-0000-000000000000	\N	\N
\.


--
-- TOC entry 4667 (class 0 OID 20332)
-- Dependencies: 239
-- Data for Name: test_script_dependencies; Type: TABLE DATA; Schema: wt2dev; Owner: wtuser_dev
--

COPY wt2dev.test_script_dependencies (test_script_dependency_id, test_script_id, depends_on_test_script_id, creation_date, created_by) FROM stdin;
\.


--
-- TOC entry 4671 (class 0 OID 20409)
-- Dependencies: 243
-- Data for Name: test_script_labels; Type: TABLE DATA; Schema: wt2dev; Owner: wtuser_dev
--

COPY wt2dev.test_script_labels (test_script_label_id, test_script_id, label_id, creation_date, created_by) FROM stdin;
\.


--
-- TOC entry 4670 (class 0 OID 20390)
-- Dependencies: 242
-- Data for Name: test_script_processes; Type: TABLE DATA; Schema: wt2dev; Owner: wtuser_dev
--

COPY wt2dev.test_script_processes (test_script_process_id, test_script_id, process_id, creation_date, created_by) FROM stdin;
\.


--
-- TOC entry 4668 (class 0 OID 20352)
-- Dependencies: 240
-- Data for Name: test_script_releases; Type: TABLE DATA; Schema: wt2dev; Owner: wtuser_dev
--

COPY wt2dev.test_script_releases (test_script_release_id, test_script_id, application_release_id, creation_date, created_by) FROM stdin;
\.


--
-- TOC entry 4669 (class 0 OID 20371)
-- Dependencies: 241
-- Data for Name: test_script_roles; Type: TABLE DATA; Schema: wt2dev; Owner: wtuser_dev
--

COPY wt2dev.test_script_roles (test_script_role_id, test_script_id, role_id, creation_date, created_by) FROM stdin;
\.


--
-- TOC entry 4666 (class 0 OID 20296)
-- Dependencies: 238
-- Data for Name: test_scripts; Type: TABLE DATA; Schema: wt2dev; Owner: wtuser_dev
--

COPY wt2dev.test_scripts (test_script_id, module_id, test_case_number, qualified_name, script_name, script_description, objective, agent_intent_name, search_document, search_vector, script_type_code, runtime_type_code, estimated_duration_seconds, display_sequence, status_code, version_no, is_deleted, deleted_date, deleted_by, creation_date, created_by, last_update_date, last_updated_by) FROM stdin;
\.


--
-- TOC entry 4675 (class 0 OID 20507)
-- Dependencies: 247
-- Data for Name: workspace; Type: TABLE DATA; Schema: wt2dev; Owner: wtuser_dev
--

COPY wt2dev.workspace (workspace_id, name, description, application_release_id, process_area_id, workspace_configurations_id, access_window_from, access_window_to, application_users, is_deleted, created_on, created_by, updated_on, updated_by, row_version) FROM stdin;
71598085-a1ff-4829-a49d-897e667cba05	Admin	Admin Module	a616351b-ad67-40c7-a9fd-b2e282a4db16	4a41ea5e-4b45-4952-922b-359a2a1217b0	956c6e56-abb1-4af9-8967-38d0e0022b3f	2026-06-10 12:43:50.081+00	2026-06-30 12:43:50.081+00	["2e02cb8a-7424-46f8-b9f2-2ca899bcd115"]	f	2026-06-10 12:47:26.882783+00	37f2450c-f3da-468d-82d7-9fc07aa1f17d	2026-06-10 13:38:08.600274+00	37f2450c-f3da-468d-82d7-9fc07aa1f17d	3
fd7b48b6-de69-4cd9-830a-01526b72036d	teststts	sadcdasasas	a616351b-ad67-40c7-a9fd-b2e282a4db16	4a41ea5e-4b45-4952-922b-359a2a1217b0	\N	2026-06-15 05:02:56.28+00	2026-06-25 05:02:56.28+00	[]	f	2026-06-15 05:08:06.754627+00	37f2450c-f3da-468d-82d7-9fc07aa1f17d	\N	\N	1
\.


--
-- TOC entry 4672 (class 0 OID 20439)
-- Dependencies: 244
-- Data for Name: workspace_configurations; Type: TABLE DATA; Schema: wt2dev; Owner: wtuser_dev
--

COPY wt2dev.workspace_configurations (workspace_configurations_id, configuration, smtp_form, parameters, is_deleted, created_on, created_by, updated_on, updated_by, row_version) FROM stdin;
956c6e56-abb1-4af9-8967-38d0e0022b3f	Prod EU	no-reply@acme.eu	[{"key": "smtp.host", "value": "smtp"}, {"key": "smtp.port", "value": "7089"}]	f	2026-06-10 10:56:22.17974+00	37f2450c-f3da-468d-82d7-9fc07aa1f17d	\N	\N	1
5b98c006-2e6f-43c1-a953-e2df59d5b876	test	test	[{"key": "host", "value": "api"}]	f	2026-06-10 10:57:10.970036+00	37f2450c-f3da-468d-82d7-9fc07aa1f17d	2026-06-10 11:26:08.482806+00	37f2450c-f3da-468d-82d7-9fc07aa1f17d	2
\.


--
-- TOC entry 4678 (class 0 OID 20602)
-- Dependencies: 250
-- Data for Name: workspace_resource; Type: TABLE DATA; Schema: wt2dev; Owner: wtuser_dev
--

COPY wt2dev.workspace_resource (workspace_resource_id, resource_id, workspace_id, is_deleted, created_on, created_by, updated_on, updated_by, row_version) FROM stdin;
69dabf72-418a-4803-8186-3e0d9284b20a	faa6f927-aeaf-465b-a135-3df4dcdc93b0	71598085-a1ff-4829-a49d-897e667cba05	f	2026-06-10 12:51:58.170844+00	37f2450c-f3da-468d-82d7-9fc07aa1f17d	\N	\N	1
\.


--
-- TOC entry 4450 (class 2606 OID 20557)
-- Name: account_history account_history_pkey; Type: CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.account_history
    ADD CONSTRAINT account_history_pkey PRIMARY KEY (account_history_id);


--
-- TOC entry 4448 (class 2606 OID 20550)
-- Name: account account_pkey; Type: CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.account
    ADD CONSTRAINT account_pkey PRIMARY KEY (account_id);


--
-- TOC entry 4365 (class 2606 OID 16836)
-- Name: acl_resource_role_details_history acl_resource_role_details_history_pkey; Type: CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.acl_resource_role_details_history
    ADD CONSTRAINT acl_resource_role_details_history_pkey PRIMARY KEY (acl_resource_role_details_history_id);


--
-- TOC entry 4362 (class 2606 OID 16800)
-- Name: acl_role_grant_policy acl_role_grant_policy_pkey; Type: CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.acl_role_grant_policy
    ADD CONSTRAINT acl_role_grant_policy_pkey PRIMARY KEY (acl_role_grant_policy_id);


--
-- TOC entry 4359 (class 2606 OID 16790)
-- Name: acl_role_master acl_role_master_pkey; Type: CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.acl_role_master
    ADD CONSTRAINT acl_role_master_pkey PRIMARY KEY (acl_role_id);


--
-- TOC entry 4389 (class 2606 OID 20231)
-- Name: application_releases application_releases_pkey; Type: CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.application_releases
    ADD CONSTRAINT application_releases_pkey PRIMARY KEY (application_release_id);


--
-- TOC entry 4444 (class 2606 OID 20474)
-- Name: application_users application_users_pkey; Type: CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.application_users
    ADD CONSTRAINT application_users_pkey PRIMARY KEY (application_users_id);


--
-- TOC entry 4373 (class 2606 OID 20140)
-- Name: applications applications_pkey; Type: CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.applications
    ADD CONSTRAINT applications_pkey PRIMARY KEY (application_id);


--
-- TOC entry 4401 (class 2606 OID 20288)
-- Name: labels labels_pkey; Type: CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.labels
    ADD CONSTRAINT labels_pkey PRIMARY KEY (label_id);


--
-- TOC entry 4385 (class 2606 OID 20207)
-- Name: modules modules_pkey; Type: CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.modules
    ADD CONSTRAINT modules_pkey PRIMARY KEY (module_id);


--
-- TOC entry 4381 (class 2606 OID 20183)
-- Name: process_areas process_areas_pkey; Type: CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.process_areas
    ADD CONSTRAINT process_areas_pkey PRIMARY KEY (process_area_id);


--
-- TOC entry 4397 (class 2606 OID 20272)
-- Name: processes processes_pkey; Type: CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.processes
    ADD CONSTRAINT processes_pkey PRIMARY KEY (process_id);


--
-- TOC entry 4442 (class 2606 OID 20458)
-- Name: resource_additional_values resource_additional_values_pkey; Type: CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.resource_additional_values
    ADD CONSTRAINT resource_additional_values_pkey PRIMARY KEY (resource_id);


--
-- TOC entry 4353 (class 2606 OID 16768)
-- Name: resource_master resource_master_employee_code_key; Type: CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.resource_master
    ADD CONSTRAINT resource_master_employee_code_key UNIQUE (employee_code);


--
-- TOC entry 4355 (class 2606 OID 16766)
-- Name: resource_master resource_master_pkey; Type: CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.resource_master
    ADD CONSTRAINT resource_master_pkey PRIMARY KEY (resource_id);


--
-- TOC entry 4393 (class 2606 OID 20254)
-- Name: roles roles_pkey; Type: CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (role_id);


--
-- TOC entry 4371 (class 2606 OID 20129)
-- Name: runtime_type_master runtime_type_master_pkey; Type: CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.runtime_type_master
    ADD CONSTRAINT runtime_type_master_pkey PRIMARY KEY (runtime_type_code);


--
-- TOC entry 4369 (class 2606 OID 20124)
-- Name: script_type_master script_type_master_pkey; Type: CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.script_type_master
    ADD CONSTRAINT script_type_master_pkey PRIMARY KEY (script_type_code);


--
-- TOC entry 4367 (class 2606 OID 20119)
-- Name: status_master status_master_pkey; Type: CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.status_master
    ADD CONSTRAINT status_master_pkey PRIMARY KEY (status_code);


--
-- TOC entry 4377 (class 2606 OID 20159)
-- Name: streams streams_pkey; Type: CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.streams
    ADD CONSTRAINT streams_pkey PRIMARY KEY (stream_id);


--
-- TOC entry 4417 (class 2606 OID 20339)
-- Name: test_script_dependencies test_script_dependencies_pkey; Type: CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.test_script_dependencies
    ADD CONSTRAINT test_script_dependencies_pkey PRIMARY KEY (test_script_dependency_id);


--
-- TOC entry 4436 (class 2606 OID 20415)
-- Name: test_script_labels test_script_labels_pkey; Type: CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.test_script_labels
    ADD CONSTRAINT test_script_labels_pkey PRIMARY KEY (test_script_label_id);


--
-- TOC entry 4432 (class 2606 OID 20396)
-- Name: test_script_processes test_script_processes_pkey; Type: CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.test_script_processes
    ADD CONSTRAINT test_script_processes_pkey PRIMARY KEY (test_script_process_id);


--
-- TOC entry 4422 (class 2606 OID 20358)
-- Name: test_script_releases test_script_releases_pkey; Type: CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.test_script_releases
    ADD CONSTRAINT test_script_releases_pkey PRIMARY KEY (test_script_release_id);


--
-- TOC entry 4427 (class 2606 OID 20377)
-- Name: test_script_roles test_script_roles_pkey; Type: CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.test_script_roles
    ADD CONSTRAINT test_script_roles_pkey PRIMARY KEY (test_script_role_id);


--
-- TOC entry 4411 (class 2606 OID 20307)
-- Name: test_scripts test_scripts_pkey; Type: CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.test_scripts
    ADD CONSTRAINT test_scripts_pkey PRIMARY KEY (test_script_id);


--
-- TOC entry 4375 (class 2606 OID 20142)
-- Name: applications uk_applications_code; Type: CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.applications
    ADD CONSTRAINT uk_applications_code UNIQUE (application_code);


--
-- TOC entry 4403 (class 2606 OID 20290)
-- Name: labels uk_label_name; Type: CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.labels
    ADD CONSTRAINT uk_label_name UNIQUE (label_name);


--
-- TOC entry 4387 (class 2606 OID 20209)
-- Name: modules uk_module_code; Type: CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.modules
    ADD CONSTRAINT uk_module_code UNIQUE (process_area_id, module_code);


--
-- TOC entry 4383 (class 2606 OID 20185)
-- Name: process_areas uk_process_area_code; Type: CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.process_areas
    ADD CONSTRAINT uk_process_area_code UNIQUE (stream_id, process_area_code);


--
-- TOC entry 4399 (class 2606 OID 20274)
-- Name: processes uk_process_code; Type: CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.processes
    ADD CONSTRAINT uk_process_code UNIQUE (process_code);


--
-- TOC entry 4391 (class 2606 OID 20233)
-- Name: application_releases uk_release_code; Type: CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.application_releases
    ADD CONSTRAINT uk_release_code UNIQUE (application_id, release_code);


--
-- TOC entry 4395 (class 2606 OID 20256)
-- Name: roles uk_role_code; Type: CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.roles
    ADD CONSTRAINT uk_role_code UNIQUE (role_code);


--
-- TOC entry 4419 (class 2606 OID 20341)
-- Name: test_script_dependencies uk_script_dependency; Type: CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.test_script_dependencies
    ADD CONSTRAINT uk_script_dependency UNIQUE (test_script_id, depends_on_test_script_id);


--
-- TOC entry 4438 (class 2606 OID 20417)
-- Name: test_script_labels uk_script_label; Type: CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.test_script_labels
    ADD CONSTRAINT uk_script_label UNIQUE (test_script_id, label_id);


--
-- TOC entry 4434 (class 2606 OID 20398)
-- Name: test_script_processes uk_script_process; Type: CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.test_script_processes
    ADD CONSTRAINT uk_script_process UNIQUE (test_script_id, process_id);


--
-- TOC entry 4424 (class 2606 OID 20360)
-- Name: test_script_releases uk_script_release; Type: CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.test_script_releases
    ADD CONSTRAINT uk_script_release UNIQUE (test_script_id, application_release_id);


--
-- TOC entry 4429 (class 2606 OID 20379)
-- Name: test_script_roles uk_script_role; Type: CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.test_script_roles
    ADD CONSTRAINT uk_script_role UNIQUE (test_script_id, role_id);


--
-- TOC entry 4379 (class 2606 OID 20161)
-- Name: streams uk_stream_code; Type: CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.streams
    ADD CONSTRAINT uk_stream_code UNIQUE (application_id, stream_code);


--
-- TOC entry 4413 (class 2606 OID 20309)
-- Name: test_scripts uk_test_case_number; Type: CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.test_scripts
    ADD CONSTRAINT uk_test_case_number UNIQUE (test_case_number);


--
-- TOC entry 4415 (class 2606 OID 20311)
-- Name: test_scripts uk_test_script_qualified_name; Type: CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.test_scripts
    ADD CONSTRAINT uk_test_script_qualified_name UNIQUE (qualified_name);


--
-- TOC entry 4440 (class 2606 OID 20450)
-- Name: workspace_configurations workspace_configurations_pkey; Type: CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.workspace_configurations
    ADD CONSTRAINT workspace_configurations_pkey PRIMARY KEY (workspace_configurations_id);


--
-- TOC entry 4446 (class 2606 OID 20519)
-- Name: workspace workspace_pkey; Type: CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.workspace
    ADD CONSTRAINT workspace_pkey PRIMARY KEY (workspace_id);


--
-- TOC entry 4453 (class 2606 OID 20610)
-- Name: workspace_resource workspace_resource_pkey; Type: CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.workspace_resource
    ADD CONSTRAINT workspace_resource_pkey PRIMARY KEY (workspace_resource_id);


--
-- TOC entry 4430 (class 1259 OID 20433)
-- Name: idx_test_script_processes_process; Type: INDEX; Schema: wt2dev; Owner: wtuser_dev
--

CREATE INDEX idx_test_script_processes_process ON wt2dev.test_script_processes USING btree (process_id);


--
-- TOC entry 4420 (class 1259 OID 20431)
-- Name: idx_test_script_releases_release; Type: INDEX; Schema: wt2dev; Owner: wtuser_dev
--

CREATE INDEX idx_test_script_releases_release ON wt2dev.test_script_releases USING btree (application_release_id);


--
-- TOC entry 4425 (class 1259 OID 20432)
-- Name: idx_test_script_roles_role; Type: INDEX; Schema: wt2dev; Owner: wtuser_dev
--

CREATE INDEX idx_test_script_roles_role ON wt2dev.test_script_roles USING btree (role_id);


--
-- TOC entry 4404 (class 1259 OID 20438)
-- Name: idx_test_scripts_agent_intent; Type: INDEX; Schema: wt2dev; Owner: wtuser_dev
--

CREATE INDEX idx_test_scripts_agent_intent ON wt2dev.test_scripts USING btree (agent_intent_name) WHERE (is_deleted = false);


--
-- TOC entry 4405 (class 1259 OID 20428)
-- Name: idx_test_scripts_module; Type: INDEX; Schema: wt2dev; Owner: wtuser_dev
--

CREATE INDEX idx_test_scripts_module ON wt2dev.test_scripts USING btree (module_id);


--
-- TOC entry 4406 (class 1259 OID 20430)
-- Name: idx_test_scripts_qualified_name; Type: INDEX; Schema: wt2dev; Owner: wtuser_dev
--

CREATE INDEX idx_test_scripts_qualified_name ON wt2dev.test_scripts USING btree (qualified_name);


--
-- TOC entry 4407 (class 1259 OID 20437)
-- Name: idx_test_scripts_script_name; Type: INDEX; Schema: wt2dev; Owner: wtuser_dev
--

CREATE INDEX idx_test_scripts_script_name ON wt2dev.test_scripts USING btree (script_name) WHERE (is_deleted = false);


--
-- TOC entry 4408 (class 1259 OID 20436)
-- Name: idx_test_scripts_search_vector; Type: INDEX; Schema: wt2dev; Owner: wtuser_dev
--

CREATE INDEX idx_test_scripts_search_vector ON wt2dev.test_scripts USING gin (search_vector);


--
-- TOC entry 4409 (class 1259 OID 20429)
-- Name: idx_test_scripts_status; Type: INDEX; Schema: wt2dev; Owner: wtuser_dev
--

CREATE INDEX idx_test_scripts_status ON wt2dev.test_scripts USING btree (status_code);


--
-- TOC entry 4363 (class 1259 OID 16826)
-- Name: uq_ix_acl_resource_role_details_active; Type: INDEX; Schema: wt2dev; Owner: wtuser_dev
--

CREATE UNIQUE INDEX uq_ix_acl_resource_role_details_active ON wt2dev.acl_resource_role_details USING btree (acl_resource_id) WHERE (is_deleted = false);


--
-- TOC entry 4360 (class 1259 OID 16791)
-- Name: uq_ix_acl_role_name_active; Type: INDEX; Schema: wt2dev; Owner: wtuser_dev
--

CREATE UNIQUE INDEX uq_ix_acl_role_name_active ON wt2dev.acl_role_master USING btree (acl_role_name) WHERE (is_deleted = false);


--
-- TOC entry 4356 (class 1259 OID 16779)
-- Name: uq_resource_email; Type: INDEX; Schema: wt2dev; Owner: wtuser_dev
--

CREATE UNIQUE INDEX uq_resource_email ON wt2dev.resource_master USING btree (email_address) WHERE (is_deleted = false);


--
-- TOC entry 4357 (class 1259 OID 16780)
-- Name: uq_resource_employee_code; Type: INDEX; Schema: wt2dev; Owner: wtuser_dev
--

CREATE UNIQUE INDEX uq_resource_employee_code ON wt2dev.resource_master USING btree (employee_code) WHERE (is_deleted = false);


--
-- TOC entry 4451 (class 1259 OID 20631)
-- Name: uq_workspace_resource; Type: INDEX; Schema: wt2dev; Owner: wtuser_dev
--

CREATE UNIQUE INDEX uq_workspace_resource ON wt2dev.workspace_resource USING btree (resource_id, workspace_id) WHERE (is_deleted = false);


--
-- TOC entry 4506 (class 2620 OID 20435)
-- Name: test_scripts trg_test_script_search_document; Type: TRIGGER; Schema: wt2dev; Owner: wtuser_dev
--

CREATE TRIGGER trg_test_script_search_document BEFORE INSERT OR UPDATE ON wt2dev.test_scripts FOR EACH ROW EXECUTE FUNCTION wt2dev.fn_build_test_script_search_document();


--
-- TOC entry 4497 (class 2606 OID 20577)
-- Name: account fk_account_client_spoc; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.account
    ADD CONSTRAINT fk_account_client_spoc FOREIGN KEY (client_spoc) REFERENCES wt2dev.resource_master(resource_id);


--
-- TOC entry 4498 (class 2606 OID 20582)
-- Name: account fk_account_created_by; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.account
    ADD CONSTRAINT fk_account_created_by FOREIGN KEY (created_by) REFERENCES wt2dev.resource_master(resource_id);


--
-- TOC entry 4500 (class 2606 OID 20592)
-- Name: account_history fk_account_history_changed_by; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.account_history
    ADD CONSTRAINT fk_account_history_changed_by FOREIGN KEY (changed_by) REFERENCES wt2dev.resource_master(resource_id);


--
-- TOC entry 4501 (class 2606 OID 20597)
-- Name: account_history fk_account_history_client_spoc; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.account_history
    ADD CONSTRAINT fk_account_history_client_spoc FOREIGN KEY (client_spoc) REFERENCES wt2dev.resource_master(resource_id);


--
-- TOC entry 4499 (class 2606 OID 20587)
-- Name: account fk_account_updated_by; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.account
    ADD CONSTRAINT fk_account_updated_by FOREIGN KEY (updated_by) REFERENCES wt2dev.resource_master(resource_id);


--
-- TOC entry 4456 (class 2606 OID 16801)
-- Name: acl_role_grant_policy fk_acl_grant_role_id; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.acl_role_grant_policy
    ADD CONSTRAINT fk_acl_grant_role_id FOREIGN KEY (acl_grant_role_id) REFERENCES wt2dev.acl_role_master(acl_role_id);


--
-- TOC entry 4457 (class 2606 OID 16806)
-- Name: acl_role_grant_policy fk_acl_target_role_id; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.acl_role_grant_policy
    ADD CONSTRAINT fk_acl_target_role_id FOREIGN KEY (acl_target_role_id) REFERENCES wt2dev.acl_role_master(acl_role_id);


--
-- TOC entry 4459 (class 2606 OID 20143)
-- Name: applications fk_app_status; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.applications
    ADD CONSTRAINT fk_app_status FOREIGN KEY (status_code) REFERENCES wt2dev.status_master(status_code);


--
-- TOC entry 4490 (class 2606 OID 20667)
-- Name: application_users fk_application_users_created_by; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.application_users
    ADD CONSTRAINT fk_application_users_created_by FOREIGN KEY (created_by) REFERENCES wt2dev.resource_master(resource_id);


--
-- TOC entry 4491 (class 2606 OID 20672)
-- Name: application_users fk_application_users_updated_by; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.application_users
    ADD CONSTRAINT fk_application_users_updated_by FOREIGN KEY (updated_by) REFERENCES wt2dev.resource_master(resource_id);


--
-- TOC entry 4475 (class 2606 OID 20347)
-- Name: test_script_dependencies fk_dependency_parent; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.test_script_dependencies
    ADD CONSTRAINT fk_dependency_parent FOREIGN KEY (depends_on_test_script_id) REFERENCES wt2dev.test_scripts(test_script_id);


--
-- TOC entry 4476 (class 2606 OID 20342)
-- Name: test_script_dependencies fk_dependency_script; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.test_script_dependencies
    ADD CONSTRAINT fk_dependency_script FOREIGN KEY (test_script_id) REFERENCES wt2dev.test_scripts(test_script_id);


--
-- TOC entry 4470 (class 2606 OID 20291)
-- Name: labels fk_label_status; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.labels
    ADD CONSTRAINT fk_label_status FOREIGN KEY (status_code) REFERENCES wt2dev.status_master(status_code);


--
-- TOC entry 4464 (class 2606 OID 20210)
-- Name: modules fk_module_process_area; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.modules
    ADD CONSTRAINT fk_module_process_area FOREIGN KEY (process_area_id) REFERENCES wt2dev.process_areas(process_area_id);


--
-- TOC entry 4465 (class 2606 OID 20215)
-- Name: modules fk_module_status; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.modules
    ADD CONSTRAINT fk_module_status FOREIGN KEY (status_code) REFERENCES wt2dev.status_master(status_code);


--
-- TOC entry 4462 (class 2606 OID 20191)
-- Name: process_areas fk_process_area_status; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.process_areas
    ADD CONSTRAINT fk_process_area_status FOREIGN KEY (status_code) REFERENCES wt2dev.status_master(status_code);


--
-- TOC entry 4463 (class 2606 OID 20186)
-- Name: process_areas fk_process_area_stream; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.process_areas
    ADD CONSTRAINT fk_process_area_stream FOREIGN KEY (stream_id) REFERENCES wt2dev.streams(stream_id);


--
-- TOC entry 4469 (class 2606 OID 20275)
-- Name: processes fk_process_status; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.processes
    ADD CONSTRAINT fk_process_status FOREIGN KEY (status_code) REFERENCES wt2dev.status_master(status_code);


--
-- TOC entry 4466 (class 2606 OID 20234)
-- Name: application_releases fk_release_application; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.application_releases
    ADD CONSTRAINT fk_release_application FOREIGN KEY (application_id) REFERENCES wt2dev.applications(application_id);


--
-- TOC entry 4467 (class 2606 OID 20239)
-- Name: application_releases fk_release_status; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.application_releases
    ADD CONSTRAINT fk_release_status FOREIGN KEY (status_code) REFERENCES wt2dev.status_master(status_code);


--
-- TOC entry 4458 (class 2606 OID 16821)
-- Name: acl_resource_role_details fk_resource; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.acl_resource_role_details
    ADD CONSTRAINT fk_resource FOREIGN KEY (acl_resource_id) REFERENCES wt2dev.resource_master(resource_id);


--
-- TOC entry 4487 (class 2606 OID 20657)
-- Name: resource_additional_values fk_resource_additional_values_created_by; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.resource_additional_values
    ADD CONSTRAINT fk_resource_additional_values_created_by FOREIGN KEY (created_by) REFERENCES wt2dev.resource_master(resource_id);


--
-- TOC entry 4488 (class 2606 OID 20662)
-- Name: resource_additional_values fk_resource_additional_values_updated_by; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.resource_additional_values
    ADD CONSTRAINT fk_resource_additional_values_updated_by FOREIGN KEY (updated_by) REFERENCES wt2dev.resource_master(resource_id);


--
-- TOC entry 4454 (class 2606 OID 16769)
-- Name: resource_master fk_resource_created_by; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.resource_master
    ADD CONSTRAINT fk_resource_created_by FOREIGN KEY (created_by) REFERENCES wt2dev.resource_master(resource_id);


--
-- TOC entry 4489 (class 2606 OID 20459)
-- Name: resource_additional_values fk_resource_id; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.resource_additional_values
    ADD CONSTRAINT fk_resource_id FOREIGN KEY (resource_id) REFERENCES wt2dev.resource_master(resource_id);


--
-- TOC entry 4455 (class 2606 OID 16774)
-- Name: resource_master fk_resource_updated_by; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.resource_master
    ADD CONSTRAINT fk_resource_updated_by FOREIGN KEY (updated_by) REFERENCES wt2dev.resource_master(resource_id);


--
-- TOC entry 4468 (class 2606 OID 20257)
-- Name: roles fk_role_status; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.roles
    ADD CONSTRAINT fk_role_status FOREIGN KEY (status_code) REFERENCES wt2dev.status_master(status_code);


--
-- TOC entry 4460 (class 2606 OID 20162)
-- Name: streams fk_stream_app; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.streams
    ADD CONSTRAINT fk_stream_app FOREIGN KEY (application_id) REFERENCES wt2dev.applications(application_id);


--
-- TOC entry 4461 (class 2606 OID 20167)
-- Name: streams fk_stream_status; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.streams
    ADD CONSTRAINT fk_stream_status FOREIGN KEY (status_code) REFERENCES wt2dev.status_master(status_code);


--
-- TOC entry 4471 (class 2606 OID 20312)
-- Name: test_scripts fk_test_script_module; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.test_scripts
    ADD CONSTRAINT fk_test_script_module FOREIGN KEY (module_id) REFERENCES wt2dev.modules(module_id);


--
-- TOC entry 4472 (class 2606 OID 20327)
-- Name: test_scripts fk_test_script_runtime; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.test_scripts
    ADD CONSTRAINT fk_test_script_runtime FOREIGN KEY (runtime_type_code) REFERENCES wt2dev.runtime_type_master(runtime_type_code);


--
-- TOC entry 4473 (class 2606 OID 20317)
-- Name: test_scripts fk_test_script_status; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.test_scripts
    ADD CONSTRAINT fk_test_script_status FOREIGN KEY (status_code) REFERENCES wt2dev.status_master(status_code);


--
-- TOC entry 4474 (class 2606 OID 20322)
-- Name: test_scripts fk_test_script_type; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.test_scripts
    ADD CONSTRAINT fk_test_script_type FOREIGN KEY (script_type_code) REFERENCES wt2dev.script_type_master(script_type_code);


--
-- TOC entry 4483 (class 2606 OID 20423)
-- Name: test_script_labels fk_tsl_label; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.test_script_labels
    ADD CONSTRAINT fk_tsl_label FOREIGN KEY (label_id) REFERENCES wt2dev.labels(label_id);


--
-- TOC entry 4484 (class 2606 OID 20418)
-- Name: test_script_labels fk_tsl_script; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.test_script_labels
    ADD CONSTRAINT fk_tsl_script FOREIGN KEY (test_script_id) REFERENCES wt2dev.test_scripts(test_script_id);


--
-- TOC entry 4481 (class 2606 OID 20404)
-- Name: test_script_processes fk_tsp_process; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.test_script_processes
    ADD CONSTRAINT fk_tsp_process FOREIGN KEY (process_id) REFERENCES wt2dev.processes(process_id);


--
-- TOC entry 4482 (class 2606 OID 20399)
-- Name: test_script_processes fk_tsp_script; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.test_script_processes
    ADD CONSTRAINT fk_tsp_script FOREIGN KEY (test_script_id) REFERENCES wt2dev.test_scripts(test_script_id);


--
-- TOC entry 4477 (class 2606 OID 20366)
-- Name: test_script_releases fk_tsr_release; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.test_script_releases
    ADD CONSTRAINT fk_tsr_release FOREIGN KEY (application_release_id) REFERENCES wt2dev.application_releases(application_release_id);


--
-- TOC entry 4479 (class 2606 OID 20385)
-- Name: test_script_roles fk_tsr_role_role; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.test_script_roles
    ADD CONSTRAINT fk_tsr_role_role FOREIGN KEY (role_id) REFERENCES wt2dev.roles(role_id);


--
-- TOC entry 4480 (class 2606 OID 20380)
-- Name: test_script_roles fk_tsr_role_script; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.test_script_roles
    ADD CONSTRAINT fk_tsr_role_script FOREIGN KEY (test_script_id) REFERENCES wt2dev.test_scripts(test_script_id);


--
-- TOC entry 4478 (class 2606 OID 20361)
-- Name: test_script_releases fk_tsr_script; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.test_script_releases
    ADD CONSTRAINT fk_tsr_script FOREIGN KEY (test_script_id) REFERENCES wt2dev.test_scripts(test_script_id);


--
-- TOC entry 4492 (class 2606 OID 20520)
-- Name: workspace fk_workspace_application_releases; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.workspace
    ADD CONSTRAINT fk_workspace_application_releases FOREIGN KEY (application_release_id) REFERENCES wt2dev.application_releases(application_release_id);


--
-- TOC entry 4493 (class 2606 OID 20530)
-- Name: workspace fk_workspace_configurations; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.workspace
    ADD CONSTRAINT fk_workspace_configurations FOREIGN KEY (workspace_configurations_id) REFERENCES wt2dev.workspace_configurations(workspace_configurations_id);


--
-- TOC entry 4485 (class 2606 OID 20637)
-- Name: workspace_configurations fk_workspace_configurations_created_by; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.workspace_configurations
    ADD CONSTRAINT fk_workspace_configurations_created_by FOREIGN KEY (created_by) REFERENCES wt2dev.resource_master(resource_id);


--
-- TOC entry 4486 (class 2606 OID 20642)
-- Name: workspace_configurations fk_workspace_configurations_updated_by; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.workspace_configurations
    ADD CONSTRAINT fk_workspace_configurations_updated_by FOREIGN KEY (updated_by) REFERENCES wt2dev.resource_master(resource_id);


--
-- TOC entry 4494 (class 2606 OID 20647)
-- Name: workspace fk_workspace_created_by; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.workspace
    ADD CONSTRAINT fk_workspace_created_by FOREIGN KEY (created_by) REFERENCES wt2dev.resource_master(resource_id);


--
-- TOC entry 4495 (class 2606 OID 20525)
-- Name: workspace fk_workspace_process_areas; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.workspace
    ADD CONSTRAINT fk_workspace_process_areas FOREIGN KEY (process_area_id) REFERENCES wt2dev.process_areas(process_area_id);


--
-- TOC entry 4502 (class 2606 OID 20621)
-- Name: workspace_resource fk_workspace_resource_created_by; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.workspace_resource
    ADD CONSTRAINT fk_workspace_resource_created_by FOREIGN KEY (created_by) REFERENCES wt2dev.resource_master(resource_id);


--
-- TOC entry 4503 (class 2606 OID 20611)
-- Name: workspace_resource fk_workspace_resource_resource; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.workspace_resource
    ADD CONSTRAINT fk_workspace_resource_resource FOREIGN KEY (resource_id) REFERENCES wt2dev.resource_master(resource_id);


--
-- TOC entry 4504 (class 2606 OID 20626)
-- Name: workspace_resource fk_workspace_resource_updated_by; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.workspace_resource
    ADD CONSTRAINT fk_workspace_resource_updated_by FOREIGN KEY (updated_by) REFERENCES wt2dev.resource_master(resource_id);


--
-- TOC entry 4505 (class 2606 OID 20616)
-- Name: workspace_resource fk_workspace_resource_workspace; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.workspace_resource
    ADD CONSTRAINT fk_workspace_resource_workspace FOREIGN KEY (workspace_id) REFERENCES wt2dev.workspace(workspace_id);


--
-- TOC entry 4496 (class 2606 OID 20652)
-- Name: workspace fk_workspace_updated_by; Type: FK CONSTRAINT; Schema: wt2dev; Owner: wtuser_dev
--

ALTER TABLE ONLY wt2dev.workspace
    ADD CONSTRAINT fk_workspace_updated_by FOREIGN KEY (updated_by) REFERENCES wt2dev.resource_master(resource_id);


--
-- TOC entry 4684 (class 0 OID 0)
-- Dependencies: 7
-- Name: SCHEMA wt2dev; Type: ACL; Schema: -; Owner: wtadmin
--

GRANT ALL ON SCHEMA wt2dev TO wtdev_role;


-- Completed on 2026-06-15 12:07:02

--
-- PostgreSQL database dump complete
--

\unrestrict Dhqcp1KyJLRmt9d4gH7wKMubS3hfvUhyEPpkrcJXavrdMaj73dg7ddcN75iduZ9

