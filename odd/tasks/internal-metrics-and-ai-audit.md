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

- [ ] **TASK-05: Implement `AuditedLayaDecisionAdapter`**
  - **Route**: direct inline
  - **Scope**: Create `src/infrastructure/adapters/laya/audited_laya_decision_adapter.py` wrapping `LayaDecisionPort`. Intercept `decide()`, measure latency, audit input sample/questions and raw output answers via `AnalysisMetricsPort`.
  - **Verification**: Unit tests in `src/infrastructure/tests/adapters/laya/test_audited_laya_decision_adapter.py`.

- [ ] **TASK-06: Implement Centralized Structured Logging Configuration**
  - **Route**: direct inline
  - **Scope**: Create `src/infrastructure/config/logging_config.py` setting up `TimedRotatingFileHandler` writing to `logs/silvina.log` with standardized log format including correlation IDs and timestamps.
  - **Verification**: Unit tests in `src/infrastructure/tests/test_logging_config.py`.

- [ ] **TASK-07: Integrate Metrics and Audited Adapters into Pipeline & Wiring**
  - **Route**: direct inline
  - **Scope**: In `AnalyzeDocumentUseCase`, initialize analysis context and record stage latencies. In `AnalyzeDocumentUseCaseWiring`, wire `SqliteAnalysisMetricsAdapter` and wrap Laya/Ollama adapters with audited decorators. Ensure `AnalyzeDocumentUseCaseWiringForTest` uses `FakeAnalysisMetricsPort`.
  - **Verification**: Unit tests in `src/infrastructure/tests/test_analyze_document_use_case_wiring.py` and `src/application/tests/test_analyze_document_use_case.py`.

- [ ] **TASK-08: Add FastAPI Request-Timing & Logging Middleware**
  - **Route**: direct inline
  - **Scope**: Add middleware in `src/infrastructure/fastapi/fastapi_app.py` recording HTTP request method, path, status, and duration in `logs/silvina.log`.
  - **Verification**: Tests in `src/infrastructure/fastapi/tests/test_middleware.py`.

- [ ] **TASK-09: End-to-End Verification & Work-Unit Commit**
  - **Route**: direct inline
  - **Scope**: Execute full pytest suite across `src/`. Verify zero regressions. Perform test analysis and assert records in `data/metrics.db` and logs in `logs/silvina.log`.
  - **Verification**: 100% test pass rate and work-unit commit.

---

## 4. Progress & Verification Log

- **Current Status**: TASK-04 complete and uncommitted. TASK-02 (`80aabbb`) and TASK-03 (`07f50e3`) committed and pushed. Standing by for explicit user authorization to commit or proceed to TASK-05.
- **Next Step**: TASK-05 (Implement `AuditedLayaDecisionAdapter`). Open item for TASK-07: fail-safe wrapper so metrics persistence errors never break an analysis.

### Verification History
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
