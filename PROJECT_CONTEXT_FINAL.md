PROJECT CONTEXT

WinfoTest AI Intent-Driven Test Script Grouping, Semantic Discovery, Script Analysis, Failure Analysis, Indexing, Guardrail Enforcement, and Future Execution Assistant

1. Project Purpose

This project is an AI-driven extension layer for WinfoTest. The assistant should allow a user to ask questions about WinfoTest test scripts using natural language and business language. The assistant must understand the user's intent, select the correct controlled internal tool, retrieve the correct information from the WinfoTest PostgreSQL database, and return structured, explainable, auditable results.

The project originally started as a semantic discovery and similarity system:

Test Script ID
    -> retrieve test script metadata
    -> retrieve related test steps
    -> generate semantic document
    -> generate embedding
    -> store vector
    -> find similar scripts


The updated direction is broader. The project must become a PostgreSQL-grounded enterprise AI assistant over WinfoTest test metadata and execution metadata.

The assistant should support:

Intent-driven grouping of test scripts.

Semantic search over scripts.

Normal script analysis and explanation.

Similar script discovery.

Failure analysis using execution result tables.

Indexing all test scripts from PostgreSQL.

Re-indexing new or changed scripts.

Vector storage for semantic search and similarity search.

Chat-style multi-turn interaction.

Conversation memory for follow-up prompts such as "run all of them".

Future execution of selected scripts or grouped scripts through the official WinfoTest system.

The assistant must not rely on hardcoded script lists, manually curated local files, static examples, fake canonical schemas, fake canonical steps, or keyword-based business routing.

PostgreSQL is the source of truth.

2. What This Project Is

This project is:

An intent-driven AI assistant over WinfoTest metadata.

A PostgreSQL-grounded semantic discovery system.

A controlled tool-based grouping and analysis engine.

A semantic indexing and vector-search engine.

A failure-analysis assistant over execution result tables.

A future bridge into WinfoTest execution APIs.

A foundation for future test recommendation, test data generation, capability discovery, and execution orchestration.

This project is not:

A generic chatbot.

A generic document RAG system.

A separate Playwright runner.

A replacement for WinfoTest.

A direct SQL generation bot.

A hardcoded report generator.

A system where the LLM directly queries the database.

A system where the LLM directly executes tests.

A system that makes itself look smart by using fake fallback data.

The LLM should reason and route. The backend should validate and execute approved tools. The repository layer should retrieve real PostgreSQL data. WinfoTest remains the system of record and future execution authority.

3. Core Business Problem

WinfoTest test scripts can have identifiers such as:

FIN.R2R.C0123
P2P (PROCURE TO PAY)-PO-0001
H2R (HIRE TO RETIRE)-HR-0014
CX.S2R.OSC.13.C.1


These identifiers are useful for traceability but not enough for business-level discovery.

Users may ask:

Group scripts by process area.
Group scripts by process.
Group scripts by module.
Group scripts by username Connor.
Show all supplier tests.
Show all onboarding tests.
Which tests take the longest?
Find tests similar to this one.
Why did this test fail?
Run all of them.


The assistant should understand these requests, map each request to an intent, choose an approved backend tool, retrieve data from PostgreSQL, and return a structured response.

4. Absolute Source-of-Truth Rule

All production data must come from the WinfoTest PostgreSQL database.

Allowed source-of-truth data sources include:

test_scripts

test_run_scripts

test_run_script_steps

test_run_script_step_results

test_runs

process_areas

processes

modules

labels

roles

test_script_processes

test_script_labels

test_script_roles

related WinfoTest tables discovered from the WinfoTest GitHub repository

Not allowed as source of truth:

Hardcoded test script examples.

Static local script files.

Manually curated script lists.

Hardcoded supplier/onboarding/payroll mappings.

LLM-generated fake database records.

Business logic implemented through keyword if/else rules.

Canonical ERP schemas defined in production Python dictionaries.

Canonical ERP steps defined in production Python dictionaries.

Mock data may exist only for local unit testing and early development.

5. Architecture Diagram

                         USER CHAT REQUEST
                                |
                                v
                      +--------------------+
                      |  LLM Intent Router |
                      +--------------------+
                                |
                                v
                      +--------------------+
                      |   Tool Registry    |
                      +--------------------+
                                |
            +-------------------+-------------------+
            |                   |                   |
            v                   v                   v
  +------------------+ +------------------+ +----------------------+
  | Semantic         | | Semantic Search  | | Script / Failure     |
  | Cluster Service  | | Service          | | Analysis Services    |
  +------------------+ +------------------+ +----------------------+
            |                   |                   |
            v                   v                   v
                    +-----------------------+
                    |   Repository Layer    |
                    | PostgreSQL Queries    |
                    +-----------------------+
                                |
                                v
                    +-----------------------+
                    | WinfoTest PostgreSQL  |
                    | Source of Truth       |
                    +-----------------------+
                                |
                                v
                    +-----------------------+
                    | Structured DB Result  |
                    +-----------------------+
                                |
                                v
                    +-----------------------+
                    | Optional LLM Summary  |
                    | / Explanation         |
                    +-----------------------+
                                |
                                v
                         USER RESPONSE


6. Semantic Indexing Architecture

WinfoTest PostgreSQL
       |
       v
Query active / changed test scripts
       |
       v
test_scripts + test_run_scripts + test_run_script_steps
       |
       v
Build structured workflow object
       |
       v
Generate semantic document using LLM
       |
       v
Generate embedding from semantic document
       |
       v
Store vector + metadata in vector store
       |
       v
Semantic search and similar-script discovery


Vector storage is an index, not the source of truth. PostgreSQL remains the source of truth.

7. Future Execution Architecture

User: "Run all of them"
       |
       v
Conversation State retrieves previous result script IDs
       |
       v
Intent Router detects execute_script_set
       |
       v
Tool Registry validates run_test_group tool
       |
       v
Permission / safety checks
       |
       v
WinfoTestExecutionClient
       |
       v
Official WinfoTest API / internal service
       |
       v
WinfoTest execution engine
       |
       v
Execution ID / status / results returned


The AI project must not directly run Playwright and must not duplicate WinfoTest execution logic.

8. PostgreSQL Relationship Resolution

The most important relationship chain is:

test_scripts
      |
      v
test_run_scripts
      |
      v
test_run_script_steps


When a user provides a test script identifier, the system should:

Locate the matching test_scripts record.

Extract script-level metadata.

Use test_script_id to locate related runtime records in test_run_scripts.

Use test_run_script_id to locate ordered steps in test_run_script_steps.

Sort steps by step_no.

Extract step descriptions, actions, input parameters, validation fields, data types, testing types, locator code, and fallback locator metadata.

Build a structured workflow representation.

Generate semantic documents or user explanations from the structured workflow representation.

The test script alone is not enough. The ordered steps explain the real workflow.

9. Intent-Driven Architecture (Meta-Tools)

The system must be intent-driven using a condensed Meta-Tool architecture. The LLM detects what the user is trying to accomplish and selects from a small, universal set of tools rather than relying on hyper-specific, hardcoded database functions.

Allowed Meta-Tools:

semantic_cluster_scripts: Handles ALL grouping, clustering, and organizing requests (e.g., by module, by risk, by user, by taxonomy).

semantic_search_tests: Handles natural language vector searches and similarity lookups.

filtered_script_lookup: Handles strict database identifier lookups.

analyze_entity: Explains script workflows or analyzes failure logs.

execute_script_set: Triggers WinfoTest execution for a target set of scripts.

Examples:

User: Group scripts by process area.
Intent: semantic_cluster_scripts
Args: concept = "process area"

User: Group tests by high risk vs low risk EU tax compliance.
Intent: semantic_cluster_scripts
Args: concept = "high risk vs low risk EU tax compliance"

User: Show supplier banking tests.
Intent: semantic_search_tests
Args: query = "supplier banking tests"

User: Run all of them.
Intent: execute_script_set
Source: previous conversation state


The backend must enforce a strict Pydantic JSON schema when parsing the LLM's meta-tool outputs. The LLM is never allowed to generate free-form markdown reports when using the clustering tool.

10. Tool Design Rule: Pydantic Enforcement & No Taxonomy Reports

Backend tools must never contain hardcoded keyword business mappings (if "supplier") and must never silently fall back to unrelated behavior when something fails.

Crucially, the LLM is strictly prohibited from generating Taxonomy Reports or free-form classification essays.

Correct meta-tool behavior (Dynamic Clustering):

The user requests a niche concept (e.g., "high risk vs low risk").

The Python backend retrieves relevant script metadata and feeds it to the LLM.

The LLM MUST output a strict JSON object mapping cluster names to script numbers, validated by a Pydantic schema (e.g., {"High Risk": ["FIN.001"], "Low Risk": ["FIN.002"]}).

Python formats the response UI, ensuring actionable execution states rather than wordy prose.

Python saves the returned UUIDs into ConversationState so the user can execute the matched cluster immediately.

There should be no silent fallback behavior. If an execution fails or no scripts match a cluster concept, return a structured error status (e.g., not_found).

11. Detailed Debugging Requirement

Every tool must support detailed debugging metadata.

Debug output should explain:

Detected intent.

Selected tool.

Parsed arguments.

Repository method called.

Important filters used.

Number of records retrieved.

Whether semantic search was used.

Whether vector search was used.

Whether LLM summarization was used.

Any ambiguity detected.

Any missing data.

Any permission/safety checks.

Execution time per stage.

Example debug object:

{
  "detected_intent": "semantic_cluster_scripts",
  "selected_tool": "semantic_cluster_scripts",
  "arguments": {
    "concept": "risk level"
  },
  "repository_methods": [
    "list_all"
  ],
  "records_retrieved": 12,
  "ambiguities": [],
  "warnings": [],
  "execution_time_ms": 184
}


Debugging should be available to developers and logs. User-facing output should be clear and not overly technical unless the user asks for debug details.

12. Core Assistant Capabilities

12.1 Semantic Search

The assistant should support queries such as:

Show supplier banking tests.
Show onboarding tests.
Find payroll setup tests.
Search for journal entry creation tests.


Semantic search flow:

User query
  -> intent router
  -> semantic_search_tests tool
  -> query embedding
  -> vector search
  -> retrieve matching scripts from PostgreSQL
  -> retrieve ordered steps
  -> LLM explanation of match reason


The response should include test script number, script name, process/process area if available, module if available, workflow summary, ordered/summarized steps, and match reason.

12.2 Normal Script Analysis

Users should be able to ask:

Explain this script.
What does FIN.R2R.C0123 do?
Walk me through the steps.
What business workflow does this validate?


The system should retrieve the script, retrieve ordered steps, generate a semantic explanation, and display the workflow.

12.3 Similar Script Discovery

Users should be able to ask:

Find tests similar to FIN.R2R.C0123.
Show related scripts.
Find duplicate or overlapping tests.


Similarity should compare semantic workflow meaning, not script numbers.

12.4 Failure Analysis

Users should be able to ask:

Why did this test fail?
Analyze recent failures.
Which steps fail most often?
Find scripts failing for similar reasons.


The system should use execution result tables and clearly separate facts from inferred possible causes.

12.5 Dynamic Semantic Clustering

Users should be able to ask for standard metadata groupings AND highly custom niche clusters:

Standard examples:

Group by process area.

Group by module.

Group by user.

Niche custom examples:

Group by high business risk vs low risk.

Group tests validating EU tax compliance vs US tax.

Group by scripts that handle bank accounts vs those that don't.

The assistant handles ALL of these via the semantic_cluster_scripts meta-tool. It uses vector search (Qdrant) to pull the most relevant scripts, feeds the workflow context to the LLM, and enforces a strict JSON output schema to dynamically bucket the scripts into logical clusters without relying on hardcoded PostgreSQL columns.

12.6 Indexing

The system must support:

Index all scripts.
Index new scripts.
Re-index changed scripts.
Refresh vector store.
Get index status.


Indexing must come from PostgreSQL rows.

13. Conversation State Requirement

The assistant must support multi-turn chat.

Example:

User: Group test scripts by username Connor.
Assistant: Returns 12 scripts and stores the result set.
User: Run all of them.
Assistant: Understands "them" means the previous 12 scripts.


Conversation state should track:

{
  "session_id": "abc123",
  "last_user_query": "Group scripts by username Connor",
  "last_intent": "semantic_cluster_scripts",
  "last_tool": "semantic_cluster_scripts",
  "last_result_label": "Clustered by username Connor",
  "last_result_script_ids": [
    "script_id_1",
    "script_id_2"
  ],
  "can_execute_previous_result": true
}


14. Semantic Document Generation

Semantic documents are central to the system.

They are used for:

semantic search

similarity search

script explanation

clustering explanations

future capability discovery

future intent generation

A semantic document should include:

test script ID

test script number

qualified name

script name

search document

process area

process

module

labels

roles

ordered workflow steps

step summary

workflow summary

inferred business objective

business entities

key actions

validation points

Semantic documents must be generated from PostgreSQL data and must not include secrets.

15. Vector Storage and Embeddings

Embeddings should be generated from semantic documents.

Do not embed only:

script ID

script number

primary keys

raw locator code

Embeddings should represent:

business meaning

workflow meaning

process context

module context

step intent

validations

actions

entities

Recommended vector database:

Qdrant


The vector database is only an index. PostgreSQL remains the source of truth.

16. Codebase Arrangement

The codebase should be arranged as follows:

app/
  main.py

  core/
    config.py
    logging.py

  clients/
    llm_client.py
    vector_client.py
    winfotest_execution_client.py

  repositories/
    db.py
    test_script_repository.py
    step_repository.py
    grouping_repository.py
    execution_repository.py
    index_repository.py
    user_repository.py

  services/
    intent_router_service.py
    tool_registry_service.py
    semantic_document_service.py
    embedding_service.py
    vector_store_service.py
    indexing_service.py
    similarity_service.py
    semantic_search_service.py
    script_analysis_service.py
    failure_analysis_service.py
    semantic_cluster_service.py
    conversation_state_service.py
    execution_orchestration_service.py
    debug_trace_service.py

  schemas/
    intent.py
    cluster.py
    test_script.py
    semantic_document.py
    similarity.py
    semantic_search.py
    failure_analysis.py
    indexing.py
    conversation.py
    execution.py
    debug.py

scripts/
  index_all_scripts.py
  index_new_scripts.py
  generate_semantic_document.py
  find_similar.py
  semantic_search.py

tests/
  test_intent_router_service.py
  test_tool_registry_service.py
  test_semantic_cluster_service.py
  test_semantic_document_service.py
  test_similarity_service.py
  test_failure_analysis_service.py
  test_conversation_state_service.py


17. Service Responsibilities

intent_router_service.py: Converts a user query into one of the 5 universal meta-intents using strict JSON tool schemas.

tool_registry_service.py: Validates meta-tool arguments using Pydantic schemas and rejects unknown requests.

semantic_cluster_service.py: Handles dynamic sorting and bucketing of scripts based on ANY arbitrary user concept, utilizing LLM-enforced JSON schema outputs.

semantic_document_service.py: Builds semantic documents from database records deterministically.

embedding_service.py: Converts semantic documents into vectors.

vector_store_service.py: Writes and searches vectors only.

indexing_service.py: Indexes all, new, or changed scripts.

semantic_search_service.py: Performs natural language vector search and similar-script discovery.

script_analysis_service.py: Explains workflow analysis.

failure_analysis_service.py: Analyzes failed script and step execution results.

conversation_state_service.py: Manages multi-turn memory and tracks last_result_script_ids so the user can execute dynamic clusters.

debug_trace_service.py: Records execution traces, timing, and errors.

execution_orchestration_service.py: Takes selected script IDs and calls the WinfoTest execution client.

18. Guardrail Enforcement Architecture

Guardrails must be enforced through code, tests, CI/pre-commit hooks, runtime validation, and review checks.

Required enforcement layers:

Documentation guardrails
    -> architecture boundaries
    -> code contracts
    -> automated tests
    -> pre-commit checks
    -> runtime validation
    -> debug traces
    -> audit logs


Guardrails are not optional recommendations. They are part of the engineering contract for this project.

19. Tool Registry Enforcement

The LLM should never directly call arbitrary functions.

The LLM should produce a structured tool request.

Example:

{
  "intent": "semantic_cluster_scripts",
  "tool": "semantic_cluster_scripts",
  "arguments": {
    "concept": "high risk tests"
  }
}


The backend must validate:

tool exists

arguments are valid

user has permission if required

tool is allowed in the current context

If the LLM requests an unknown tool, reject it.

20. Pydantic Schema Enforcement

Every tool must have validated input and output schemas.

Do not trust raw LLM JSON.

Required flow:

LLM output
    -> JSON parse
    -> Pydantic validation
    -> tool execution


If validation fails, return a structured validation error. Every service should expose typed inputs and typed outputs.

21. Repository-Only Database Access Enforcement

Only repository files may directly access SQLAlchemy sessions or execute database queries.

Allowed:

app/repositories/*.py


Not allowed:

semantic_document_service.py running raw SQL
intent_router_service.py running raw SQL
llm_client.py running raw SQL
vector_store_service.py querying PostgreSQL directly


Services should call repositories. Repositories should query PostgreSQL.

22. No Hardcoded Business Logic Enforcement

The codebase must be scanned for banned patterns.

Examples of banned production patterns:

CANONICAL_ERP_SCHEMAS
CANONICAL_ERP_STEPS
if "supplier"
if "invoice"
if "employee"
if "payroll"
default to POSITIVE_HAPPY_PATH
fallback to all scripts
return all scripts when lookup fails


A guardrail script should exist:

scripts/check_guardrails.py


This script should fail when banned patterns are found in production code.

Allowed exceptions:

unit tests

documentation examples

explicit mock data folders

23. No Silent Fallback Enforcement

Every tool must return a clear status.

Allowed statuses:

success
not_found
ambiguous
insufficient_data
unauthorized
service_unavailable
validation_error
internal_error


Bad behavior:

user not found -> return all scripts
Qdrant unavailable -> silently use keyword search
script not found -> return first script


Correct behavior:

{
  "status": "not_found",
  "message": "No test scripts found matching that concept",
  "debug": {
    "tool": "semantic_cluster_scripts",
    "concept": "high risk",
    "records_found": 0
  }
}


24. Debug Trace Enforcement

Every tool must return or log a debug trace.

Debug trace should include:

trace_id

detected_intent

selected_tool

parsed_arguments

repository_methods

records_retrieved

vector_search_used

llm_used

warnings

errors

duration_ms

Debug traces are required for enterprise troubleshooting.

25. Vector Store Enforcement

The vector store must never silently fall back to in-memory mode in production.

Allowed behavior:

ENV=local      -> local disk vector store allowed
ENV=test       -> in-memory vector store allowed
ENV=production -> persistent vector store required


If production lacks persistent vector configuration, fail fast.

Every vector point must include:

point_type

test_script_id

semantic_document_hash

embedding_model

embedding_dimension

indexed_at

source_updated_at

Allowed point types:

parent_script
step_chunk
failure_summary


Do not cluster mixed vector types unless explicitly intended.

26. PostgreSQL Source-of-Truth Enforcement

After vector search, reload script IDs from PostgreSQL.

Correct flow:

vector search -> script IDs -> PostgreSQL reload -> final response


Do not produce final user-facing answers from vector payloads alone.

27. LLM Client Enforcement

The LLM client must support:

API key validation

timeout handling

retry handling

rate-limit handling

structured JSON generation

Pydantic validation

prompt/version tracking

trace ID support

safe error classes

logging of duration and model used

A simple re-export file is not enough unless the canonical client implements all of the above.

28. ORM Enforcement

SQLAlchemy models must match the real PostgreSQL schema.

Do not invent simplified table names.

Do not alias runtime tables to unrelated conceptual tables.

Correct relationship chain:

test_scripts
    -> test_run_scripts
    -> test_run_script_steps
    -> test_run_script_step_results


If WinfoTest uses a schema such as wt2dev, SQLAlchemy must be configured to use that schema correctly.

SQLite tests are useful but not enough. Repository correctness must be verified against PostgreSQL or a PostgreSQL test container.

29. AI-Owned Table Boundary Enforcement

Core WinfoTest tables should be treated as source-of-truth tables.

AI-owned tables should be clearly separated.

Recommended AI-owned table names:

ai_semantic_documents
ai_vector_index_status
ai_discovery_logs
ai_conversation_sessions
ai_tool_audit_logs


Do not casually write AI-generated records into core WinfoTest tables.

30. Pre-Commit Enforcement

A pre-commit hook should run guardrail checks before code is committed.

Recommended hook:

python scripts/check_guardrails.py


This should catch:

hardcoded ERP schemas

hardcoded ERP steps

suspicious keyword routing

direct SQL outside repositories

production in-memory vector fallback

prompt-only services

unsafe tool names

31. Pull Request Checklist

Every pull request should include this checklist:

No hardcoded ERP schemas
No hardcoded canonical steps
No keyword-based supplier/invoice/payroll routing
No silent fallbacks
No direct LLM SQL
No direct Playwright execution
No secrets in prompts, logs, embeddings, or vectors
Vector payload has point_type
PostgreSQL remains source of truth
LLM output is Pydantic validated
Tool returns debug trace
Repository-only database access
Unit tests added or updated


32. Runtime Audit Enforcement

Every tool call should eventually be logged to an AI-owned audit table.

Recommended table:

ai_tool_audit_logs


Recommended fields:

audit_id
timestamp
session_id
user_id
intent
tool_name
arguments_json
status
records_returned
duration_ms
error_message
trace_id


This allows the team to answer:

Why did the AI return these scripts?
What tool was used?
What data was queried?
What failed?


33. Read-Only Default Enforcement

Until WinfoTest integration is formally approved, default system behavior should be read-only.

Allowed writes:

ai_semantic_documents
ai_vector_index_status
ai_tool_audit_logs
ai_conversation_sessions


Not allowed without approval:

test_scripts
test_run_scripts
test_run_script_steps
workspace_configurations
core WinfoTest execution tables


34. Immediate MVP After Refactor

The first refactored version should support:

Connect to PostgreSQL.

Retrieve a test script by identifier.

Retrieve related runtime script records.

Retrieve ordered test steps.

Generate a semantic document.

Generate an embedding.

Store a vector.

Index all scripts.

Re-index new or changed scripts.

Perform semantic search.

Find similar scripts.

Analyze one script normally.

Analyze failures from execution result tables.

Group and cluster scripts dynamically via the LLM meta-tools based on any criteria.

Route chat requests through a controlled tool registry.

Maintain conversation state for follow-up prompts.

Provide detailed debugging traces for tool execution.

Run guardrail checks through tests/pre-commit.

Execution through WinfoTest should be designed as an interface but may remain stubbed until WinfoTest API integration is understood.

35. Security Rules

The assistant must never:

Run arbitrary SQL from LLM output.

Access secrets.

Embed passwords.

Expose credentials.

Call execution APIs without permission checks.

Execute tests directly through Playwright.

Bypass WinfoTest authorization.

Silently fall back to broad or unrelated results.

The backend must:

Validate every tool call.

Sanitize configuration data.

Restrict tool execution.

Log tool usage.

Keep secrets out of semantic documents.

Keep secrets out of vector storage.

Use repositories instead of raw LLM-generated SQL.

Return structured error/ambiguity results instead of guessing.

36. Final Mission Statement

Build a PostgreSQL-grounded, intent-driven enterprise AI assistant for WinfoTest that can understand user requests, select controlled dynamic meta-tools, retrieve and analyze real WinfoTest test script data, generate semantic documents, store vectors, perform semantic search, find similar scripts, analyze failures, cluster scripts dynamically using AI classification, preserve conversation state, enforce enterprise guardrails, provide detailed debugging traces, and eventually execute selected test scripts through the official WinfoTest system.