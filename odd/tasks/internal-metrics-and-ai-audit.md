# Feature: Internal Metrics and AI Audit

- **Feature Name**: `internal-metrics-and-ai-audit`
- **File Locator**: `odd/tasks/internal-metrics-and-ai-audit.md`
- **TDD Mode**: Enabled (Strict TDD: RED -> GREEN -> REFACTOR)
- **TDD Runner**: `.venv/Scripts/python -m pytest src/`
- **Delivery Strategy**: `ask-on-risk`
- **Forecast Changed Lines**: ~400 lines
- **Running Authored Lines**: 0

---

## 1. Objective & Problem
`silvina-editorial` lacks internal observability and metrics. There is currently no record of execution latencies per pipeline stage, no persistence of the prompts and raw responses exchanged with Ollama and Laya, and no structured logging of errors and HTTP requests.

This feature introduces a 100% self-contained, open-source, and free observability and telemetry subsystem based on:
1. **Local SQLite (`data/metrics.db`) with WAL mode** to record document analysis summaries (master) and full AI interactions (detail: prompts, questions, text samples, raw model outputs, and latencies).
2. **Infrastructure Decorators** wrapping `LlmGeneratorPort` and `LayaDecisionPort` to intercept inputs and outputs cleanly without polluting domain services.
3. **Correlation ID context (`AnalysisContextPort` + `AnalysisContextAdapter`)** using Python's standard `contextvars` to link AI interactions to the specific document analysis without changing domain method signatures.
4. **Structured rotating file logging** (`logs/silvina.log`) and a FastAPI request-timing middleware to track API traffic and system events.

---

## 2. Scope & Constraints

### In Scope
- Define `AnalysisMetricsPort` in the domain/application layer and a test double `FakeAnalysisMetricsPort`.
- Define `AnalysisContextPort` in the domain and implement `AnalysisContextAdapter` in infrastructure using `contextvars` to manage execution/analysis IDs.
- Implement `SqliteAnalysisMetricsAdapter` in infrastructure with SQLite WAL mode and relational tables: `analyses` (master) and `ai_interactions` (detail).
- Implement `AuditedLlmGeneratorAdapter` wrapping `LlmGeneratorPort` to capture Ollama prompts, raw responses, and latencies.
- Implement `AuditedLayaDecisionAdapter` wrapping `LayaDecisionPort` to capture Laya text samples, questions, raw decision dictionaries, and latencies.
- Implement centralized structured logging in `src/infrastructure/config/logging_config.py` with `TimedRotatingFileHandler`.
- Wire `SqliteAnalysisMetricsAdapter` and the audited decorators into `AnalyzeDocumentUseCaseWiring` and `AnalyzeDocumentUseCase`.
- Add a lightweight request logging middleware in `src/infrastructure/fastapi/fastapi_app.py`.
- Comprehensive unit and integration test suite with zero regressions across `src/`.

### Out of Scope
- External database servers (PostgreSQL, MySQL).
- Heavy external observability stacks (Docker, Prometheus daemon, Grafana server).
- Breaking existing domain public interfaces or existing tests.

---

## 3. Checklist of Actionable Tasks

- [x] **TASK-01: Define domain port `AnalysisMetricsPort`, domain service `AnalysisMetricsRecorder`, DTOs, and test double**
  - **Route**: subagent delegation (`gentle-ai-worker`)
  - **Scope**: Under `src/domain/dtos/`, create `AnalysisStartDTO`, `StageDurationDTO`, `AiInteractionDTO`, and `AnalysisCompletionDTO` inheriting from `BaseDTO`. Under `src/domain/metrics/`, create `AnalysisMetricsPort(ABC)` with abstract methods accepting single DTO parameters: `record_analysis_start(start_data: AnalysisStartDTO)`, `record_stage_duration(stage_duration: StageDurationDTO)`, `record_ai_interaction(ai_interaction: AiInteractionDTO)`, and `record_analysis_completion(completion_data: AnalysisCompletionDTO)`. Create domain service `AnalysisMetricsRecorder` wrapping `AnalysisMetricsPort`. Create test double `src/domain/tests/metrics/fake_analysis_metrics_port.py`.
  - **Verification**: Unit tests in `src/domain/tests/dtos/` (12 passed) and `src/domain/tests/metrics/` (10 passed) — 22 passed total.
  - **Outcome**: Created all DTOs and interfaces with single-parameter contracts, strictly complying with Clean Architecture and parameter-object conventions. Full test suite: 770 passed in 9.18s.

- [x] **TASK-02: Implement `AnalysisContextPort` and `AnalysisContextAdapter` using `contextvars`**
  - **Route**: subagent delegation (`gentle-ai-worker`)
  - **Scope**: Under `src/domain/metrics/`, create `AnalysisContextPort(ABC)` with `get_analysis_id() -> str | None`, `set_analysis_id(analysis_id: str)` and `clear_analysis_id()`. Under `src/infrastructure/adapters/metrics/`, create `AnalysisContextAdapter` backed by a class-level `contextvars.ContextVar` shared by all instances. Create test double `src/domain/tests/metrics/fake_analysis_context_port.py`. Consumers (audited adapters, recorder, use case) receive the port through their constructors instead of calling global functions.
  - **Verification**: Unit tests in `src/domain/tests/metrics/test_analysis_context_port.py` (7 passed) and `src/infrastructure/tests/adapters/metrics/test_analysis_context_adapter.py` (9 passed).
  - **Outcome**: Initial attempt used module-level functions with global state in `src/application/`; it was discarded because it did not fit the clean-architecture skill (everything is a class, collaborators are injected). Replaced with port + adapter + fake. Full test suite: 723 passed.

- [x] **TASK-03: Implement `SqliteAnalysisMetricsAdapter`**
  - **Route**: subagent delegation (`gentle-ai-worker`)
  - **Scope**: Create `src/infrastructure/adapters/metrics/sqlite_analysis_metrics_adapter.py` fulfilling `AnalysisMetricsPort`. Configure `PRAGMA journal_mode = WAL;`. Create tables `analyses`, `stage_durations` and `ai_interactions` on init (`stage_durations` added because `StageDurationDTO` needs a persistence target). Implement parameterized synchronous SQL inserts, one short-lived connection per operation (FastAPI serves requests from threads), no foreign keys so telemetry ordering problems cannot break an analysis. The constructor receives `database_path`; the default `data/metrics.db` and `EnvConfig` entry are wired in TASK-07.
  - **Verification**: Unit tests in `src/infrastructure/tests/adapters/metrics/test_sqlite_analysis_metrics_adapter.py` (14 passed) verifying schema creation, WAL pragma, idempotent init, upsert on completion, parameterization against SQL injection, large unicode payloads, insertion order and committed visibility.
  - **Outcome**: Completion is an UPSERT that preserves the original `started_at` when the start was recorded and fills it when it was not. Duplicate `analysis_id` on start raises `sqlite3.IntegrityError` (propagates). Full test suite: 737 passed.

- [x] **TASK-04: Implement `AuditedLlmGeneratorAdapter`**
  - **Route**: subagent delegation (`gentle-ai-worker`)
  - **Scope**: Create `src/infrastructure/adapters/llm_generator/audited_llm_generator_adapter.py` wrapping `LlmGeneratorPort`. Constructor receives `generator`, `metrics_port: AnalysisMetricsPort`, `analysis_context_port: AnalysisContextPort`, `provider`, `model_name` and `purpose` (the domain port cannot tell who is calling, so TASK-07 builds one audited instance per consumer with its own `purpose`). Intercept `generate()`, measure latency, record prompt as `input_payload` and the raw response as `output_payload` via `AnalysisMetricsPort`; when the wrapped generator fails, record `status="error"` with `ExceptionType: message` and re-raise the same exception object. Without an active analysis id the interaction is recorded under `unassigned`. Failures of the metrics port itself propagate (a fail-safe metrics wrapper is planned for TASK-07). Test doubles `FailingLlmGeneratorAdapter` and `SlowLlmGeneratorAdapter` live in `src/infrastructure/tests/test_doubles/`.
  - **Verification**: Unit tests in `src/infrastructure/tests/adapters/llm_generator/test_audited_llm_generator_adapter.py` (14 passed).
  - **Outcome**: Decorator records one `AiInteractionDTO` per call (success or error) and leaves the wrapped behavior untouched. Full test suite: 751 passed.

- [ ] **TASK-05: Implement `AuditedLayaDecisionAdapter`** (DEFERRED)
  - **Blocker**: `LayaDecisionPort`, `LayaDecisionResultDTO` and the Laya adapter only exist in `feat/laya-system-one-ports` (29 commits ahead, not an ancestor of this branch). Decision (user): postpone until this branch is rebased onto Laya once Laya is merged; this branch stays Laya-free. The Laya part of TASK-07 (wrapping the Laya adapter) is deferred together with it.
  - **Route**: direct inline
  - **Scope**: Create `src/infrastructure/adapters/laya/audited_laya_decision_adapter.py` wrapping `LayaDecisionPort`. Intercept `decide()`, measure latency, audit input sample/questions and raw output answers via `AnalysisMetricsPort`.
  - **Verification**: Unit tests in `src/infrastructure/tests/adapters/laya/test_audited_laya_decision_adapter.py`.

- [x] **TASK-06: Implement Centralized Structured Logging Configuration**
  - **Route**: subagent delegation (`gentle-ai-worker`)
  - **Scope**: Create `LoggingConfig` in `src/infrastructure/config/logging_config.py` (constructor receives `log_file_path`, `log_level`, `backup_count` and `AnalysisContextPort`; `configure()` attaches a midnight-rotating UTF-8 `TimedRotatingFileHandler` to the root logger, idempotently, failing fast on an invalid level). Create `AnalysisContextLogFilter` in `src/infrastructure/config/analysis_context_log_filter.py`, attached to the handler so every child logger record carries `analysis_id` (or `-`). Format: `%(asctime)s | %(levelname)s | %(name)s | analysis_id=%(analysis_id)s | %(message)s` with ISO timestamps including timezone offset. Callers (entry points), `EnvConfig` entries (`LOG_FILE_PATH` default `logs/silvina.log`, level, retention) and the wiring are TASK-07/08. `.gitignore` now ignores `logs/` and `data/metrics.db*`.
  - **Verification**: Unit tests in `src/infrastructure/tests/test_logging_config.py` and `src/infrastructure/tests/test_analysis_context_log_filter.py` (12 passed).
  - **Outcome**: Until now the project called `getLogger` in several modules but no handler was configured anywhere; this task provides the single configuration point. Full test suite: 763 passed.

- [x] **TASK-10: Privacy mode `APP_MODE` (DEBUG | PROD) for AI payload auditing** (inserted; done BEFORE TASK-07)
  - **Origin**: `silvina-doc/prd.md:22` requires data privacy (100% local flow, unpublished manuscripts). The audit stores full prompts/responses (manuscript text) in `data/metrics.db`, which must not happen in production. User decision: an `.env` parameter `APP_MODE` with values `DEBUG` or `PROD`; in `DEBUG` privacy rules are not applied (full prompts and responses are needed to diagnose the LLM), in `PROD` they are.
  - **Route**: subagent delegation (`gentle-ai-worker`)
  - **Scope**: Domain enum `AppMode` (`DEBUG`, `PROD`) in `src/domain/enums/`. Domain service `AuditPayloadPolicy(app_mode)` in `src/domain/metrics/` with a single method that receives a raw payload and returns the payload to persist: in `DEBUG` the payload unchanged; in `PROD` the marker `[REDACTED chars=N sha256=<hex>]` (no content, size and hash kept for traceability). Latency, model, provider, purpose and status are always persisted. `EnvConfig.app_mode` read from `APP_MODE`, default `PROD` (fails closed on privacy), case-insensitive, any other value fails fast. `AuditedLlmGeneratorAdapter` receives the policy by constructor and applies it to `input_payload` and to `output_payload` (also the error text, which may echo content). The future audited Laya adapter (TASK-05) must use the same policy. The user adds `APP_MODE` to `.env`/`.env.example` by hand (security policy blocks reading `.env*`).
  - **Refinement**: in the error path the exception TYPE name stays visible in every mode (`ErrorType: [REDACTED ...]` in PROD); only the message passes through the policy. The value returned to the caller and the re-raised exception are never altered. `openspec/specs/analyze-document/spec.md` documents `APP_MODE` in the environment-variable table.
  - **Outcome**: Full test suite: 794 passed (21 new). `.env.example` carries `APP_MODE=DEBUG` (user edit, committed with this task) while the code default is `PROD`.
  - **Out of scope**: the request middleware (TASK-08) never logs query string, headers or body in any mode.
  - **Verification**: Unit tests for the enum, the policy (both modes, unicode, empty payload, hash determinism), `EnvConfig.app_mode` (default, case-insensitive, invalid value) and the updated audited adapter tests.

- [x] **TASK-07: Integrate Metrics and Audited Adapters into Pipeline & Wiring** (split in three sub-steps; Laya part deferred with TASK-05)
  - **Route**: subagent delegation (`gentle-ai-worker`), one worker per sub-step
  - **Design**: the use case never touches ports (skill), so it receives a domain service `AnalysisTracker` that owns the analysis lifecycle. The use case is a singleton served from threads, hence the tracker keeps NO per-analysis state on the instance: the analysis id lives in `AnalysisContextPort` and timings in local variables. `AnalyzeDocumentUseCaseWiringForTest` does not exist on this branch (it lives in the Laya branch) and is NOT created here to avoid an add/add conflict on integration; wiring tests override the infrastructure methods inline.
  - [x] **07a** Domain service `AnalysisTracker` (`track_analysis(document_name, pipeline)`: new `uuid4().hex` id, context set, start recorded with the file base name only, pipeline run, completion recorded as `success` or `error`, original exception re-raised, context always cleared; `measure_stage(stage_name)` context manager recording duration even if the stage fails and nothing when no analysis is active) and `FailSafeAnalysisMetricsAdapter` (decorator that turns any metrics-port failure into a WARNING without payload, so telemetry never breaks an analysis). Test double `FailingAnalysisMetricsPort`. 22 new tests.
    - **Refinement (user decision: no hardcoded constants)**: domain values are enums, not strings. New enum `ExecutionStatus` (`RUNNING`, `SUCCESS`, `ERROR`) in `src/domain/enums/`. `AnalysisCompletionDTO` is typed `word_count: int | None`, `char_count: int | None`, `article_type: ArticleType | None`, `verdict: PublicationVerdict | None`, `status: ExecutionStatus`, and `AiInteractionDTO.status` is `ExecutionStatus`. A failed analysis records `None` (stored as SQL NULL) instead of the magic values `0`/`"unknown"`/`"unavailable"`, because those data do not exist at that point. `SqliteAnalysisMetricsAdapter` persists enum `.value` through one `_enum_value` helper; `AuditedLlmGeneratorAdapter` and `AnalysisTracker` use the enum members. This changes the contract of the TASK-01 DTOs. Remaining named constants are infrastructure formatting/sentinels (`unassigned`, `-`, log and date formats). Full suite: 823 passed.
  - [x] **07b** `EnvConfig` entries: `METRICS_DATABASE_PATH` and `LOG_FILE_PATH` have NO default and are REQUIRED (user decision: machine-specific paths; a missing, empty or whitespace-only value fails fast with `Required environment variable <NAME> is not set` through one private `_get_required_env`), `LOG_LEVEL` (default `INFO`, independent of `APP_MODE`) and `LOG_RETENTION_DAYS` (default 14). `LoggingConfigWiring.create_logging_config()` assembles `LoggingConfig` with `AnalysisContextAdapter` and is invoked as the first action of `main()` in `web_main.py` and `main.py` (before `uvicorn.run`). Root `conftest.py` points both required variables to a temporary folder for the whole session and has an `autouse` fixture `isolate_root_logger` that removes and closes any handler a test attached to the root logger and restores its level: the existing tests under `tests/` call the real `main()` and `web_main.main()`, which now run `configure()`, and without it the handler kept `silvina.log` locked (`PermissionError` when the temporary folder is removed) and a stray `logs/silvina.log` could appear in the repository. Spec table has the four rows (`— (required)` for the two paths). The user adds the four variables to `.env.example` and `.env` by hand. Full repository suite: 889 passed (`src/` 846, `tests/` 43). Known pre-existing type-checker finding (not introduced here, left untouched on purpose): `TextIO.reconfigure` in `main.py` and `conftest.py`. To verify in TASK-09 with a real run: that the file handler survives `uvicorn.run`'s own `dictConfig`.
  - [x] **07c-1** (inserted, user preference: no hardcoded domain strings) Enums `AnalysisStage` (ten pipeline stages), `AiProvider` (`OLLAMA` only; `LAYA` is added with TASK-05 once Laya is integrated) and `AiPurpose` (`ARTICLE_CLASSIFICATION`, `QUALITY_ANALYSIS`, `EDITORIAL_SUITABILITY`) in `src/domain/enums/`. `StageDurationDTO.stage_name`, `AiInteractionDTO.provider`/`purpose`, `AnalysisTracker.measure_stage` and `AuditedLlmGeneratorAdapter` are typed with them; `SqliteAnalysisMetricsAdapter` stores their `.value`. Pure refactor; full repository suite 905 passed.
  - [x] **07c-2** `AnalyzeDocumentUseCase` receives `AnalysisTracker` and wraps each pipeline stage with `measure_stage`; `execute` delegates to `track_analysis`. `AnalyzeDocumentUseCaseWiring` builds `AnalysisContextAdapter`, `SqliteAnalysisMetricsAdapter` wrapped by `FailSafeAnalysisMetricsAdapter`, one shared `AuditPayloadPolicy(env_config.app_mode)` and one `AuditedLlmGeneratorAdapter` per LLM consumer (purposes `AiPurpose.ARTICLE_CLASSIFICATION`, `AiPurpose.QUALITY_ANALYSIS`, `AiPurpose.EDITORIAL_SUITABILITY`, provider `AiProvider.OLLAMA`; stages use `AnalysisStage`). The test `test_article_classifier_and_quality_analyzer_share_llm_generator` must be rewritten: consumers now share the underlying Ollama generator, not the audited instance. **Outcome**: `AnalyzeDocumentUseCase.execute` keeps `@generic_error_handler` and delegates to `AnalysisTracker.track_analysis`; the old body is `_run_pipeline` with the ten stages measured in pipeline order. **Refinement (single-responsibility, user concern)**: the first version wrapped each stage in a `with ...measure_stage(...)` block, which put ten blocks of instrumentation noise and an extra indentation level in the orchestrator. `AnalysisTracker.track_stage(stage_name, operation, **arguments)` (built on `measure_stage`, same guarantees: duration recorded even if the operation raises, nothing recorded without an active analysis) lets each stage be ONE call of the same shape as the original code, and `measure_stage` no longer appears in the use case. Considered and discarded: extracting the instrumented pipeline into another domain class (moves the noise, adds a class) and decorating collaborators from the wiring (they are concrete domain classes, not ports; would need new interfaces). The wiring builds one shared `FailSafeAnalysisMetricsAdapter(SqliteAnalysisMetricsAdapter(METRICS_DATABASE_PATH))`, one shared `AuditPayloadPolicy(APP_MODE)`, and one `AuditedLlmGeneratorAdapter` per consumer over the same `OllamaGeneratorAdapter`. Tests: stage order and ids, error path with `ExecutionStatus.ERROR`, context cleared, wiring of purposes/provider/model, shared metrics port and policy, and two wiring-level integration tests (PROD redacted payloads and DEBUG full payloads read back from a real SQLite file). Full repository suite: 921 passed. Laya wrapping stays deferred with TASK-05.
  - **Verification**: Unit tests in `src/infrastructure/tests/test_analyze_document_use_case_wiring.py` and `src/application/tests/test_analyze_document_use_case.py`.

- [x] **TASK-08: Add FastAPI Request-Timing & Logging Middleware**
  - **Route**: subagent delegation (`gentle-ai-worker`)
  - **Scope**: `RequestTimingMiddleware` in `src/infrastructure/fastapi/src/middleware/request_timing_middleware.py`, a pure ASGI middleware (not `BaseHTTPMiddleware`, so streamed report downloads stay unbuffered), registered in `create_app` right after `register_exception_handlers`. It emits one INFO record per HTTP request: `request method=... path=... status=... duration_ms=...`; an exception from the app is logged as 500 and re-raised untouched; lifespan/websocket scopes pass through. Query string, headers and body are never logged. Records reach `logs/silvina.log` once `LoggingConfig` is invoked from the entry points (TASK-07). `/static/...` requests are logged too (may be lowered to DEBUG if noisy).
  - **Verification**: Tests in `src/infrastructure/fastapi/tests/test_middleware.py` (10 passed).
  - **Outcome**: Full test suite: 773 passed.

- [x] **TASK-09: End-to-End Verification & Work-Unit Commit** (real runs done; Laya part pending with TASK-05)
  - **Route**: direct inline (verification only, no code changes)
  - **Scope**: Execute the full suite and real runs. Evidence (2026-10-01, scratch folders for `METRICS_DATABASE_PATH` and `LOG_FILE_PATH`, deleted afterwards):
    - Full repository suite: 921 passed.
    - Programmatic check: the `TimedRotatingFileHandler` survives uvicorn's own `dictConfig` (root handler kept; lines written before and after).
    - Real server (`web_main.py`): the database is created at startup; one `request method=... path=... status=... duration_ms=...` line per request including 404s; the query string never appears (`?secreto=abc123` logged as the bare path); server stopped, port freed.
    - Real CLI analysis, `APP_MODE=PROD` (document `1. test_Cientifico.docx`, Ollama 0.35.0, model `hf.co/unsloth/gemma-4-26B-A4B-it-GGUF:UD-IQ4_XS`, 5 m 38 s): `journal_mode=wal`; one `analyses` row `success` (3613 words, 26235 chars, `aprobado`); ten `stage_durations` rows in pipeline order; five `ai_interactions` (`article_classification`, 2x `quality_analysis`, 2x `editorial_suitability`, provider `ollama`) all with payloads stored as `[REDACTED chars=N sha256=...]`; same `analysis_id` in analyses, stages, AI interactions and the log lines; last log line (after the analysis) has `analysis_id=-`.
    - Real CLI analysis with Ollama unreachable (`OLLAMA_BASE_URL` to a closed port, `APP_MODE=DEBUG`): CLI behavior unchanged (error message, exit code 1); `analyses` row `error` with NULL counts/type/verdict; stages recorded up to and including the failing `classify_article`; one `ai_interactions` row `error` with `LanguageModelUnavailable: ` and the FULL prompt (8885 chars).
    - Real CLI analysis, `APP_MODE=DEBUG` on the same database: full prompts and full model responses stored (0 redacted rows); two analyses (error + success) coexist.
    - Privacy: no manuscript text (checked distinctive prompt strings) in either log file, including the error traceback.
  - **Findings and resolution**: (1) FIXED: the ERROR record written by `@generic_error_handler` carries `analysis_id=-` because `track_analysis` clears the context before the exception reaches the decorator, so the failure could not be joined with its `analyses` row. `AnalysisTracker.track_analysis` now logs one ERROR record (`Analysis failed with <ExceptionType> after <n> ms`, exception TYPE only, never the message) while the id is still bound; verified in real runs: its `analysis_id` equals the `analyses.analysis_id`. (2) FIXED: in DEBUG the stored error text was empty (`LanguageModelUnavailable: `). `AuditedLlmGeneratorAdapter._describe_exception` now records the whole `__cause__` chain (`Type: msg <- caused by Type: msg`), cycle-safe, with every message passed through `AuditPayloadPolicy` (PROD: type names visible, messages as `[REDACTED ...]`); verified in real runs in both modes. Regression test with a real `LoggingConfig`: `src/infrastructure/tests/test_analysis_failure_log_correlation.py`. The `generic_error_handler` lines still show `analysis_id=-` by design (they run after the context is cleared). (3) ACCEPTED: root level INFO also writes one `httpx` line per Ollama call; lower `LOG_LEVEL` is not needed, filter if it becomes noisy. Full repository suite after the fixes: 931 passed.
  - **Verification**: 100% test pass rate; work-unit commits already pushed per task.

---

## 4. Progress & Verification Log

- **Current Status**: TASK-02, 03, 04, 06, 08, 10, 07a, 07b and 07c-1 committed and pushed to `origin/feat/internal-metrics-and-ai-audit` (last pushed commit `4dd6feb`). TASK-07c-2 complete and uncommitted. TASK-05 deferred (needs Laya). Standing by for explicit user authorization to commit.
- **Next Step**: TASK-09 (end-to-end verification with a real run: records in `data/metrics.db`, lines in `logs/silvina.log`, handler survives `uvicorn.run`'s `dictConfig`, request middleware lines, `APP_MODE` PROD vs DEBUG payloads). TASK-05 and the Laya part of the wiring after Laya is integrated.

### Verification History
- **TASK-10**: Complete (uncommitted).
  - RED: 36 failed / 18 passed across the new and updated test modules (missing enum, policy, `EnvConfig.app_mode`, un-redacted adapter payloads).
  - GREEN: Implemented `AppMode`, `AuditPayloadPolicy`, `EnvConfig.app_mode` and the policy in `AuditedLlmGeneratorAdapter`. 54 tests passed in the touched modules. Full test suite: 794 passed. `ruff check` and `ruff format --check` clean.
  - Verification: PROD never exposes original content (marker only, characters counted not bytes, deterministic sha256), DEBUG passthrough, fail-closed default, fail-fast on invalid or empty `APP_MODE`, no inline comments.
- **TASK-08**: Complete (uncommitted).
  - RED: `.venv/Scripts/python -m pytest src/infrastructure/fastapi/tests/test_middleware.py` failed with `ModuleNotFoundError: No module named 'src.infrastructure.fastapi.src.middleware'`.
  - GREEN: Implemented `RequestTimingMiddleware` and registered it in `create_app`. 10 tests passed. Full test suite: 773 passed. `ruff check` and `ruff format --check` clean.
  - Verification: pure ASGI, one class per file, no inline comments, PEP 257 docstrings, query string never logged, downstream exceptions propagate.
- **TASK-06**: Complete (uncommitted).
  - RED: `.venv/Scripts/python -m pytest src/infrastructure/tests/test_logging_config.py src/infrastructure/tests/test_analysis_context_log_filter.py` failed with `ModuleNotFoundError: No module named 'src.infrastructure.config.logging_config'`.
  - GREEN: Implemented `LoggingConfig` and `AnalysisContextLogFilter`. 12 tests passed. Full test suite: 763 passed. `ruff check` and `ruff format --check` clean.
  - Verification: `unittest.TestCase`, no inline comments, PEP 257 docstrings, no `basicConfig`/`print`, collaborators injected by constructor, handler cleanup in test `tearDown` to avoid Windows file locks.
- **TASK-04**: Complete (uncommitted).
  - RED: `.venv/Scripts/python -m pytest src/infrastructure/tests/adapters/llm_generator/test_audited_llm_generator_adapter.py` failed with `ModuleNotFoundError: No module named 'src.infrastructure.adapters.llm_generator.audited_llm_generator_adapter'`.
  - GREEN: Implemented `AuditedLlmGeneratorAdapter`. 14 tests passed. Full test suite: 751 passed. `ruff check` and `ruff format --check` clean.
  - Verification: `unittest.TestCase`, no inline comments, PEP 257 docstrings, no `@generic_error_handler`, original exception re-raised untouched, `_ms` suffix kept for durations.
- **TASK-03**: Complete (uncommitted).
  - RED: `.venv/Scripts/python -m pytest src/infrastructure/tests/adapters/metrics/test_sqlite_analysis_metrics_adapter.py` failed with `ModuleNotFoundError: No module named 'src.infrastructure.adapters.metrics.sqlite_analysis_metrics_adapter'`.
  - GREEN: Implemented `SqliteAnalysisMetricsAdapter`. 14 tests passed. Full test suite: 737 passed. `ruff check` and `ruff format --check` clean.
  - Verification: `unittest.TestCase`, no inline comments, PEP 257 docstrings, parameterized queries only, no `@generic_error_handler` on the adapter, infrastructure imports domain only.
- **TASK-02**: Complete (uncommitted).
  - Redesign: the first implementation (module-level functions in `src/application/analysis_context.py`, 714 tests passing) was replaced because it held global state outside any injectable class and violated the clean-architecture skill.
  - RED: `.venv/Scripts/python -m pytest src/domain/tests/metrics/test_analysis_context_port.py src/infrastructure/tests/adapters/metrics/test_analysis_context_adapter.py` failed with `ModuleNotFoundError: No module named 'src.domain.metrics.analysis_context_port'`.
  - GREEN: Implemented `AnalysisContextPort`, `AnalysisContextAdapter` and `FakeAnalysisContextPort`. 16 tests passed. Full test suite: 723 passed.
  - Verification: `unittest.TestCase`, no inline comments, PEP 257 docstrings, domain imports only stdlib, infrastructure imports domain, shared context across adapter instances and isolation through `copy_context()` covered.
- **TASK-01**: Complete.
  - RED: `.venv/Scripts/python -m pytest src/domain/tests/metrics/` failed with `ModuleNotFoundError: No module named 'src.domain.metrics'`.
  - GREEN: Implemented `AnalysisMetricsPort(ABC)`, `AnalysisMetricsRecorder`, and `FakeAnalysisMetricsPort`. 10 tests passed in `src/domain/tests/metrics/`. Full test suite: 758 passed in 19.44s.
  - Verification: Clean architecture rules strictly verified: domain folder `src/domain/metrics/`, domain service with no `Service` suffix, `unittest.TestCase` format, and DTOs extending `BaseDTO`. Zero regressions. Commit: `19ec559`.
