# Project Reuse Minimal Pipeline

## TL;DR
> **Summary**: Rebuild the legacy football betting flow as a minimal, provider-agnostic Python pipeline under `src/`, preserving only the reusable domain capabilities: match fetching, odds JSON parsing, CSV persistence, prompt construction, LLM invocation abstraction, and structured output parsing.
> **Deliverables**:
> - New `src/` package for the end-to-end pipeline
> - Two-layer CSV flow: raw capture CSV + normalized CSV
> - Prompt template assets migrated into the new package
> - Provider-agnostic LLM interface with test double
> - Tests-after coverage under `src/tests/`
> - Single entrypoint that runs fetch → CSV → prompt → LLM → parse
> **Effort**: Large
> **Parallel**: YES - 2 waves
> **Critical Path**: 1 → 2/3 → 4/5 → 6/7 → 8

## Context
### Original Request
- Based on `PROJECT_REUSE_ANALYSIS.md`, complete the whole task as a new implementation.
- Put the related code under `src/`.

### Interview Summary
- Scope is the **minimal runnable pipeline only**; no CLI expansion, no web/API layer, no scheduler, no MySQL.
- LLM integration must be **provider-agnostic** rather than locked to DashScope/Qwen.
- Verification strategy is **tests-after** plus agent-executed QA scenarios.
- CSV output must use **two layers**: a raw fetch CSV and a normalized CSV.

### Metis Review (gaps addressed)
- Added an explicit **LLM abstraction boundary** so implementation cannot regress into vendor-specific coupling.
- Added a required **fake/in-memory LLM test double** to make tests deterministic without external API calls.
- Added a strict fixture rule: use **synthetic or sanitized samples only**; do not couple tests to production credentials or live network.
- Added guardrails preventing accidental reintroduction of Flask routes, DB writes, scheduler logic, or hardcoded secrets.

## Work Objectives
### Core Objective
Create a decision-complete implementation plan for a new Python pipeline under `src/` that:
1. Fetches match list data from the external sporttery API.
2. Fetches odds details for the selected matches.
3. Writes raw API-derived records to CSV.
4. Normalizes records into a stable CSV schema.
5. Builds a prompt from normalized rows.
6. Calls a provider-agnostic LLM client.
7. Parses the model output into structured betting suggestions.

### Deliverables
- `src/` package scaffold for the pipeline
- Match-list fetch module
- Odds-detail fetch module
- Odds normalization/parser module
- CSV IO module for raw + normalized layers
- Prompt asset + prompt builder module
- LLM interface, fake provider, and output parser
- Pipeline entrypoint module
- Tests under `src/tests/`

### Definition of Done (verifiable conditions with commands)
- `src/` contains the full runnable implementation and no new application logic is added outside `src/`.
- The pipeline can run from a single entrypoint command and produce both raw and normalized CSV outputs.
- Prompt generation uses the migrated template contract and normalized CSV data rather than MySQL queries.
- LLM integration is abstracted behind an interface and supports a fake provider for tests.
- Parsing rejects malformed LLM output and validates money totals.
- All tests pass via a single test command.
- No code path imports Flask, APScheduler, or `pymysql`.

### Must Have
- Internal naming stays `snake_case`.
- New logic lives in `src/`.
- CSV schema is dict-first and explicit; no positional list contracts.
- Tests use fixtures that are synthetic or sanitized.
- Environment variables hold any provider-specific credentials.

### Must NOT Have (guardrails, AI slop patterns, scope boundaries)
- Must NOT recreate Flask routes or Blueprints.
- Must NOT recreate MySQL insert/update/query flows.
- Must NOT recreate APScheduler, lock-file orchestration, or shell deployment scripts.
- Must NOT hardcode API keys, model names, passwords, or absolute local paths.
- Must NOT preserve legacy list-index data shapes from `crawl_insert.py`.
- Must NOT make tests depend on live external APIs or real LLM providers.
- Must NOT place new business logic in repo root files such as `app.py`.

## Verification Strategy
> ZERO HUMAN INTERVENTION — all verification is agent-executed.
- Test decision: tests-after + `pytest` (to be added if absent) with tests located under `src/tests/`
- QA policy: Every task includes agent-executed happy-path and failure/edge scenarios
- Evidence: `.sisyphus/evidence/task-{N}-{slug}.{ext}`

## Execution Strategy
### Parallel Execution Waves
> Target: 5-8 tasks per wave. <3 per wave (except final) = under-splitting.
> Extract shared dependencies as Wave-1 tasks for max parallelism.

Wave 1: foundation and contracts
- Task 1: Scaffold `src/` package, runtime config, and shared data models
- Task 2: Implement match list fetch client
- Task 3: Implement odds detail fetch client and raw CSV writer
- Task 4: Implement odds normalization parser

Wave 2: composition and verification
- Task 5: Implement normalized CSV schema reader/writer
- Task 6: Implement prompt assets and prompt builder
- Task 7: Implement LLM abstraction, fake provider, and result parser
- Task 8: Implement pipeline orchestration and full tests-after coverage

### Dependency Matrix (full, all tasks)
| Task | Depends On | Enables |
|---|---|---|
| 1 | None | 2, 3, 4, 5, 6, 7, 8 |
| 2 | 1 | 3, 8 |
| 3 | 1, 2 | 4, 5, 8 |
| 4 | 1, 3 | 5, 6, 8 |
| 5 | 1, 4 | 6, 8 |
| 6 | 1, 5 | 8 |
| 7 | 1 | 8 |
| 8 | 1, 2, 3, 4, 5, 6, 7 | Final Verification |

### Agent Dispatch Summary
| Wave | Task Count | Categories |
|---|---:|---|
| Wave 1 | 4 | quick, unspecified-low, unspecified-high |
| Wave 2 | 4 | quick, writing, unspecified-high, deep |
| Final Verification | 4 | oracle, unspecified-high, deep |

## TODOs
> Implementation + Test = ONE task. Never separate.
> EVERY task MUST have: Agent Profile + Parallelization + QA Scenarios.

- [ ] 1. Scaffold the new `src/` package and shared contracts

  **What to do**:
  - Create the new package structure under `src/` as the only location for new application logic.
  - Add shared modules for configuration loading, filesystem path constants, and typed/dict-based contracts.
  - Standardize the runtime output locations for CSV artifacts outside code, e.g. `data/raw_matches.csv` and `data/normalized_matches.csv`, while keeping the implementation itself under `src/`.
  - Define canonical record shapes for:
    - match list items
    - raw odds payload rows
    - normalized odds rows
    - parsed suggestion rows
  - Add package-level entrypoint conventions so later tasks can import stable interfaces instead of cross-module internals.

  **Must NOT do**:
  - Do not import or wrap `app.py`, Flask, Blueprints, scheduler code, or any MySQL code.
  - Do not hardcode provider names or credentials in config defaults.

  **Recommended Agent Profile**:
  - Category: `quick` — Reason: bounded scaffold and contract setup across a small number of files
  - Skills: `[]` — no extra skill is required
  - Omitted: `['git-master']` — no git operation is part of this task

  **Parallelization**: Can Parallel: NO | Wave 1 | Blocks: 2, 3, 4, 5, 6, 7, 8 | Blocked By: none

  **References** (executor has NO interview context — be exhaustive):
  - Analysis: `PROJECT_REUSE_ANALYSIS.md:407-515` — recommended new module split and minimal-chain architecture
  - Analysis: `PROJECT_REUSE_ANALYSIS.md:518-549` — explicit migration principles and exclusions
  - Legacy architecture: `README.md:1-58` — confirms repo is still rooted in Flask/MySQL and should not be mirrored
  - Legacy anti-pattern to avoid: `app.py:1-17` — top-level Flask/bootstrap coupling to exclude

  **Acceptance Criteria** (agent-executable only):
  - [ ] `src/` contains a coherent package scaffold with shared contracts and config modules.
  - [ ] No newly created file under `src/` imports `flask`, `pymysql`, or `flask_apscheduler`.
  - [ ] Output paths for raw and normalized CSV are defined in one centralized place.

  **QA Scenarios** (MANDATORY — task incomplete without these):
  ```
  Scenario: Scaffold imports resolve
    Tool: Bash
    Steps: Run `python -m compileall src` and then import the shared package root in a one-shot Python command.
    Expected: Compilation succeeds and import raises no syntax/import error.
    Evidence: .sisyphus/evidence/task-1-scaffold.txt

  Scenario: Forbidden legacy deps absent
    Tool: Bash
    Steps: Run a Python script that recursively inspects `src/**/*.py` for forbidden imports: `flask`, `pymysql`, `flask_apscheduler`.
    Expected: Zero forbidden imports found.
    Evidence: .sisyphus/evidence/task-1-scaffold-error.txt
  ```

  **Commit**: YES | Message: `feat(src): scaffold minimal pipeline package` | Files: `src/**`

- [ ] 2. Implement the match list fetch client

  **What to do**:
  - Rebuild the reusable logic from the legacy match-list crawler as a pure client module under `src/`.
  - Replace the legacy “parallel lists” return contract with a list of dict records containing at least `match_id`, `match_date`, `sections_no_1`, `league_id`, and `season_id`.
  - Preserve the rolling date-range iteration behavior from the legacy implementation.
  - Add explicit HTTP error handling, timeouts, and response validation.
  - Make request/session behavior injectable for tests so no test depends on live network.

  **Must NOT do**:
  - Do not print directly as a control-flow mechanism.
  - Do not return tuple/list shapes copied from the legacy implementation.

  **Recommended Agent Profile**:
  - Category: `unspecified-low` — Reason: network client rewrite with schema cleanup and testability requirements
  - Skills: `[]` — standard Python work
  - Omitted: `['git-master']` — no git action needed

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: 3, 8 | Blocked By: 1

  **References**:
  - Legacy source: `crawler/crawler_all_match_id.py:6-20` — `get_match_id` extraction behavior to preserve semantically
  - Legacy source: `crawler/crawler_all_match_id.py:23-40` — request endpoint and request parameter pattern
  - Legacy source: `crawler/crawler_all_match_id.py:43-100` — rolling-window crawl logic and multi-league iteration
  - Analysis: `PROJECT_REUSE_ANALYSIS.md:44-73` — why these functions are the correct reusable foundation

  **Acceptance Criteria**:
  - [ ] A fetch function can request match-list data for a date range using injected HTTP behavior.
  - [ ] A parse function returns dict-based match records with no positional indexing.
  - [ ] Invalid or non-200 responses raise/return a controlled domain error path instead of silent corruption.

  **QA Scenarios**:
  ```
  Scenario: Parse valid match list payload
    Tool: Bash
    Steps: Run a pytest case using a mocked HTTP response with at least 2 matches across one date window.
    Expected: The client returns the expected list of dicts with stable keys and correct IDs/dates.
    Evidence: .sisyphus/evidence/task-2-match-list.txt

  Scenario: Remote API failure is surfaced cleanly
    Tool: Bash
    Steps: Run a pytest case with mocked 500/timeout behavior.
    Expected: The client emits a controlled exception/result and writes no partial CSV output.
    Evidence: .sisyphus/evidence/task-2-match-list-error.txt
  ```

  **Commit**: YES | Message: `feat(src): add match list fetch client` | Files: `src/**`

- [ ] 3. Implement the odds detail fetch client and raw CSV writer

  **What to do**:
  - Rebuild the odds detail retrieval flow under `src/` for a list of match IDs.
  - Persist the **raw** layer to CSV as one row per match with the original payload preserved in a serializable column set (or normalized JSON string column) plus basic fetch metadata.
  - Record fetch failures/skips deterministically so downstream normalization can distinguish “missing data” from “not fetched”.
  - Make the raw writer idempotent for a single pipeline run and stable across repeated test executions.

  **Must NOT do**:
  - Do not bring over any insert/update DB function from `crawl_insert.py`.
  - Do not drop incomplete matches silently.

  **Recommended Agent Profile**:
  - Category: `unspecified-high` — Reason: combines API retrieval, durable raw storage design, and failure-accounting behavior
  - Skills: `[]` — standard Python work
  - Omitted: `['git-master']` — no git action needed

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: 4, 5, 8 | Blocked By: 1, 2

  **References**:
  - Legacy source: `crawler/crawl_insert.py:136-179` — restore/skip behavior and per-match fetch loop to preserve conceptually
  - Legacy source: `crawler/crawl_insert.py:146-179` — endpoint, request params, and batching behavior
  - Analysis: `PROJECT_REUSE_ANALYSIS.md:76-119` — odds detail extraction is core reusable knowledge
  - Analysis: `PROJECT_REUSE_ANALYSIS.md:451-459` — CSV should replace DB as the storage layer

  **Acceptance Criteria**:
  - [ ] Odds detail fetching works from a list of match IDs using injected HTTP behavior.
  - [ ] A raw CSV artifact is created with enough data to re-run normalization offline.
  - [ ] Skip/failure state is explicit and testable.

  **QA Scenarios**:
  ```
  Scenario: Raw odds payloads are persisted
    Tool: Bash
    Steps: Run a pytest case with 2 mocked match IDs and successful mocked odds responses, then inspect the generated raw CSV fixture output.
    Expected: The raw CSV contains 2 rows with match IDs and payload/fetch metadata columns populated.
    Evidence: .sisyphus/evidence/task-3-raw-csv.txt

  Scenario: Incomplete payload is marked, not lost
    Tool: Bash
    Steps: Run a pytest case where one mocked odds response is missing one or more required odds blocks.
    Expected: The raw CSV captures the failed/skipped state explicitly and downstream code can identify it without guessing.
    Evidence: .sisyphus/evidence/task-3-raw-csv-error.txt
  ```

  **Commit**: YES | Message: `feat(src): add odds fetch and raw csv output` | Files: `src/**`

- [ ] 4. Implement the normalized odds parser

  **What to do**:
  - Rebuild the legacy parsing knowledge from `get_had`, `get_hhad`, `get_ttg`, `get_hafu`, `get_crs`, `get_meta`, and `restore_data` into a dict-first normalization module.
  - Parse the latest odds entry per play type by `updateDate` + `updateTime` semantics.
  - Convert legacy positional arrays into named keys such as `had_h`, `had_d`, `had_a`, `ttg_s0`…`ttg_s7`, `crs_1_0`, etc.
  - Keep normalization logic pure so it can consume raw CSV rows offline without refetching.
  - Define and document behavior for missing sections: fail-fast vs marked invalid record; do not leave it implicit.

  **Must NOT do**:
  - Do not emit nested anonymous lists.
  - Do not mix normalization with file IO or LLM prompt formatting.

  **Recommended Agent Profile**:
  - Category: `unspecified-high` — Reason: dense domain mapping with many fields and high error risk
  - Skills: `[]` — standard Python work
  - Omitted: `['git-master']` — no git action needed

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: 5, 6, 8 | Blocked By: 1, 3

  **References**:
  - Legacy source: `crawler/crawl_insert.py:7-36` — `get_had` and `get_hhad` latest-entry extraction
  - Legacy source: `crawler/crawl_insert.py:39-69` — `get_ttg` and `get_hafu` field mapping
  - Legacy source: `crawler/crawl_insert.py:72-143` — `get_crs`, `get_meta`, `restore_data`
  - Analysis: `PROJECT_REUSE_ANALYSIS.md:98-118` — target shape should move from list indices to dict-based structured fields
  - Analysis: `PROJECT_REUSE_ANALYSIS.md:429-448` — parser should become dedicated `odds_parser`-style module

  **Acceptance Criteria**:
  - [ ] Normalization converts a raw odds payload into a stable dict schema with named fields.
  - [ ] Latest-entry selection is deterministic and covered by tests.
  - [ ] Missing required odds groups produce a controlled invalid-record outcome.

  **QA Scenarios**:
  ```
  Scenario: Normalize complete payload successfully
    Tool: Bash
    Steps: Run a pytest case using a sanitized complete raw payload fixture.
    Expected: The normalized dict includes meta fields and all required named odds fields with expected values.
    Evidence: .sisyphus/evidence/task-4-normalize.txt

  Scenario: Missing odds block is rejected predictably
    Tool: Bash
    Steps: Run a pytest case with a raw payload missing `crsList` or another required section.
    Expected: The parser returns/raises a defined invalid-record result rather than partial, ambiguous data.
    Evidence: .sisyphus/evidence/task-4-normalize-error.txt
  ```

  **Commit**: YES | Message: `feat(src): add normalized odds parser` | Files: `src/**`

- [ ] 5. Implement normalized CSV writer and reader

  **What to do**:
  - Define the canonical normalized CSV column order based on the parser output and prompt needs.
  - Add IO helpers that write normalized rows and read them back as dict records without schema drift.
  - Ensure the reader can load all rows or filter by `match_id`.
  - Add schema validation so malformed normalized CSV fails loudly.
  - Keep the normalized CSV suitable for both prompt generation and regression tests.

  **Must NOT do**:
  - Do not infer columns dynamically from one arbitrary row.
  - Do not depend on pandas unless there is a repository-wide reason; use standard-library CSV unless a concrete blocker appears.

  **Recommended Agent Profile**:
  - Category: `quick` — Reason: bounded schema + IO task with deterministic behavior
  - Skills: `[]` — no extra skill needed
  - Omitted: `['git-master']` — no git action needed

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: 6, 8 | Blocked By: 1, 4

  **References**:
  - Analysis: `PROJECT_REUSE_ANALYSIS.md:260-279` — reuse the “map by column names” idea, but rewrite for CSV
  - Analysis: `PROJECT_REUSE_ANALYSIS.md:451-464` — CSV module responsibilities and field design guidance
  - Prompt sample: `prompt_data_input.txt:1-57` — indicates which normalized fields must be available to prompt generation

  **Acceptance Criteria**:
  - [ ] The normalized CSV schema is explicitly defined in code and reused by writer and reader.
  - [ ] Reader output matches writer input semantically for a round trip.
  - [ ] Missing required columns produce a deterministic schema error.

  **QA Scenarios**:
  ```
  Scenario: Normalized CSV round-trip works
    Tool: Bash
    Steps: Run a pytest case that writes normalized rows to a temp CSV and reads them back.
    Expected: The read-back rows match the source records for required fields.
    Evidence: .sisyphus/evidence/task-5-normalized-csv.txt

  Scenario: Schema drift is rejected
    Tool: Bash
    Steps: Run a pytest case against a malformed CSV missing one required column.
    Expected: The reader fails with a clear schema error instead of silently returning partial rows.
    Evidence: .sisyphus/evidence/task-5-normalized-csv-error.txt
  ```

  **Commit**: YES | Message: `feat(src): add normalized csv io` | Files: `src/**`

- [ ] 6. Implement prompt assets and prompt builder

  **What to do**:
  - Migrate the reusable prompt contract into the new `src/` package as package-owned assets or constants.
  - Rebuild `get_match_data_prompt` and `enhance_prompt` as pure functions that take normalized row dicts and a money amount.
  - Preserve the numbered play ordering and wording contract needed by downstream output parsing.
  - Make prompt construction deterministic, including newline formatting and section ordering.
  - Support generating prompt text from one normalized match record without DB access.

  **Must NOT do**:
  - Do not query MySQL or depend on team-name lookup through legacy tables.
  - Do not couple prompt generation to a specific LLM provider SDK.

  **Recommended Agent Profile**:
  - Category: `writing` — Reason: prompt asset migration plus strict text-format contract
  - Skills: `[]` — no extra skill needed
  - Omitted: `['git-master']` — no git action needed

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: 8 | Blocked By: 1, 5

  **References**:
  - Legacy source: `app.py:215-286` — `get_match_data_prompt` ordering and textual phrasing to preserve semantically
  - Legacy source: `app.py:291-330` — `enhance_prompt` envelope to convert into pure template logic
  - Prompt asset: `prompt_template.txt:1-36` — source template contract
  - Prompt sample: `prompt_data_input.txt:1-57` — example of expected data block format
  - Analysis: `PROJECT_REUSE_ANALYSIS.md:152-190` — prompt logic should be rewritten around CSV rows

  **Acceptance Criteria**:
  - [ ] A pure function can build the per-match odds text block from one normalized row.
  - [ ] A pure function can wrap that block into the full prompt with a provided money amount.
  - [ ] Prompt output retains the numbered play contract expected by the parser.

  **QA Scenarios**:
  ```
  Scenario: Prompt generated from normalized row
    Tool: Bash
    Steps: Run a pytest case with a sanitized normalized-row fixture and `money=200`.
    Expected: The generated prompt includes the team names, numbered play lines, and the final format instruction with `%%` markers described.
    Evidence: .sisyphus/evidence/task-6-prompt.txt

  Scenario: Missing required normalized field fails early
    Tool: Bash
    Steps: Run a pytest case with a normalized row missing a required odds field.
    Expected: Prompt building fails with a clear validation error rather than producing a malformed prompt.
    Evidence: .sisyphus/evidence/task-6-prompt-error.txt
  ```

  **Commit**: YES | Message: `feat(src): add prompt builder` | Files: `src/**`

- [ ] 7. Implement provider-agnostic LLM abstraction, fake provider, and result parser

  **What to do**:
  - Define an abstract LLM client interface in `src/` that accepts prompt text and returns raw model text.
  - Add at least one fake/in-memory provider implementation for deterministic tests.
  - Implement provider-specific adapters only behind the abstraction boundary; credentials and model identifiers must come from environment-backed config.
  - Rebuild the legacy `re_extract` logic as a pure parser that:
    - extracts the `%%...%%` segment
    - parses each bracketed bet line
    - validates the total amount equals the requested money
    - returns a structured list of suggestion dicts
  - Define explicit parser errors for malformed formatting, missing markers, and incorrect money totals.

  **Must NOT do**:
  - Do not hardcode any API key or default provider secret.
  - Do not return Flask `jsonify(...)` or other HTTP-layer artifacts.

  **Recommended Agent Profile**:
  - Category: `unspecified-high` — Reason: abstraction boundary + deterministic testing + strict text parsing
  - Skills: `[]` — standard Python work
  - Omitted: `['git-master']` — no git action needed

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: 8 | Blocked By: 1

  **References**:
  - Legacy source: `app.py:178-208` — current LLM call shape and embedded `re_extract` logic
  - Analysis: `PROJECT_REUSE_ANALYSIS.md:194-255` — LLM call should become pure module logic and parser should return structured Python objects
  - Analysis: `PROJECT_REUSE_ANALYSIS.md:483-499` — `llm_client.py` responsibilities and config direction

  **Acceptance Criteria**:
  - [ ] LLM invocation is defined behind an interface with at least one fake provider implementation.
  - [ ] A parser can convert valid model text into structured suggestion rows.
  - [ ] Missing `%%` markers or incorrect total amount trigger explicit parser failures.

  **QA Scenarios**:
  ```
  Scenario: Fake provider drives deterministic success path
    Tool: Bash
    Steps: Run a pytest case using the fake provider to return a valid `%%...%%` suggestion payload.
    Expected: The parser returns structured suggestions and validates the exact total money.
    Evidence: .sisyphus/evidence/task-7-llm.txt

  Scenario: Malformed model output is rejected
    Tool: Bash
    Steps: Run a pytest case with fake-provider text missing `%%` markers or using a wrong money total.
    Expected: The parser fails with a defined error type/message and no partial suggestion result.
    Evidence: .sisyphus/evidence/task-7-llm-error.txt
  ```

  **Commit**: YES | Message: `feat(src): add llm abstraction and parser` | Files: `src/**`

- [ ] 8. Implement the end-to-end pipeline entrypoint and tests-after coverage

  **What to do**:
  - Add a single entrypoint module under `src/` that orchestrates the full flow:
    1. fetch match list
    2. fetch odds details
    3. write raw CSV
    4. normalize and write normalized CSV
    5. read normalized CSV
    6. build prompt
    7. call LLM through the abstraction
    8. parse and emit final structured suggestions
  - Make the pipeline composable so tests can run the full flow with mocked network and fake LLM.
  - Add tests-after coverage under `src/tests/` for unit and end-to-end happy/error paths.
  - Ensure the pipeline can target one match deterministically in tests and can surface failures without partial silent success.

  **Must NOT do**:
  - Do not add a Flask endpoint, web server, or scheduler as the orchestration surface.
  - Do not require live credentials or a real network for the end-to-end test suite.

  **Recommended Agent Profile**:
  - Category: `deep` — Reason: integration choreography across all modules with deterministic end-to-end verification
  - Skills: `[]` — standard Python work
  - Omitted: `['git-master']` — no git action needed

  **Parallelization**: Can Parallel: NO | Wave 2 | Blocks: Final Verification | Blocked By: 1, 2, 3, 4, 5, 6, 7

  **References**:
  - Analysis: `PROJECT_REUSE_ANALYSIS.md:502-515` — `main.py` should stitch the full minimal chain together
  - Analysis: `PROJECT_REUSE_ANALYSIS.md:520-549` — preserve domain knowledge, rewrite architecture shell
  - Legacy anti-pattern to replace: `app.py:166-212` — current route-coupled end-to-end flow
  - Prompt builder source: `app.py:215-330` — prompt construction to be reused only as pure-function logic

  **Acceptance Criteria**:
  - [ ] A single entrypoint runs the full pipeline using the new `src/` modules only.
  - [ ] The pipeline produces both raw and normalized CSV outputs in one run.
  - [ ] An end-to-end test can execute the entire flow with mocked HTTP + fake LLM and assert the final structured suggestion payload.
  - [ ] Failure in fetch, normalization, or parser stages surfaces as a controlled failure with no ambiguous partial success.

  **QA Scenarios**:
  ```
  Scenario: End-to-end pipeline succeeds offline
    Tool: Bash
    Steps: Run the full pytest suite including an end-to-end test that uses mocked HTTP responses and the fake LLM provider.
    Expected: Tests pass, both CSV artifacts are created in temp/output paths, and the final parsed suggestions match the expected structured result.
    Evidence: .sisyphus/evidence/task-8-pipeline.txt

  Scenario: End-to-end pipeline fails cleanly on malformed LLM output
    Tool: Bash
    Steps: Run an end-to-end pytest case with valid mocked fetch data but fake-provider output that violates the `%%` contract.
    Expected: The pipeline aborts with a defined parser failure and does not report a success result.
    Evidence: .sisyphus/evidence/task-8-pipeline-error.txt
  ```

  **Commit**: YES | Message: `feat(src): add end-to-end minimal pipeline` | Files: `src/**`

## Final Verification Wave (MANDATORY — after ALL implementation tasks)
> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.
> **Do NOT auto-proceed after verification. Wait for user's explicit approval before marking work complete.**
> **Never mark F1-F4 as checked before getting user's okay.** Rejection or user feedback -> fix -> re-run -> present again -> wait for okay.
- [ ] F1. Plan Compliance Audit — oracle
- [ ] F2. Code Quality Review — unspecified-high
- [ ] F3. Real Manual QA — unspecified-high (+ playwright if UI)
- [ ] F4. Scope Fidelity Check — deep

## Commit Strategy
- Prefer one commit per numbered task after task-local tests pass.
- Keep commit messages aligned with the task messages above.
- Do not combine unrelated modules into one commit.
- Do not commit generated CSV runtime artifacts unless the repo explicitly wants checked-in fixtures.

## Success Criteria
- The new implementation is fully centered in `src/`.
- The minimal chain from external API fetch to structured LLM suggestion is runnable without Flask/MySQL.
- Raw and normalized CSV layers are both implemented and test-covered.
- Prompt generation and output parsing preserve the useful business contract from the legacy project while removing old framework coupling.
- LLM integration is provider-agnostic and testable offline via a fake provider.
- The test suite and scripted QA scenarios verify both happy and failure paths without human intervention.
