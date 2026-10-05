# Feature: Tests Must Never Write the Real Metrics Database

- **Feature Name**: `test-database-isolation`
- **File Locator**: `odd/tasks/test-database-isolation.md`
- **Branch**: `feat/configurable-text-limits` (the user's working branch; follows `d285db9`)
- **TDD Mode**: Test-first (RED then GREEN); the invariant tests fail today under `unittest`
- **TDD Runner**: `export APP_MODE=PROD; .venv/Scripts/python.exe -m unittest discover -s src -t . -p "test_*.py"` and the same with `-s tests` (do NOT invoke a test module directly). No `USE_EXTERNAL_LLM` / `METRICS_DATABASE_PATH` overrides must be needed anymore.
- **Commit policy**: no commit until the user orders it; one task at a time, wait for the user's approval before the next task or the verifier
- **Edit-tool restriction**: the agent cannot edit `.env` or `.env.example`

---

## 1. Objective

The test suite must never write `data/metrics.db` (nor `logs/silvina.log`), whichever runner is used.

## 2. Evidence

- `conftest.py` already isolates the metrics database, the log file, `TESTING` and `USE_EXTERNAL_LLM`, but only `pytest` loads it. The documented runner is `unittest discover`, which ignores it, so the wiring read the real `.env` (`METRICS_DATABASE_PATH=data/metrics.db`).
- On 2026-10-05 `data/metrics.db` held 92 test analyses, 460 linked and 69 `unassigned` AI rows and 920 stage rows written by the suite (cleaned the same day, backup kept). Tests that reach the real wiring: `tests/e2e/test_fastapi_e2e.py`, `tests/smoke/test_classify_article_parity.py`, `src/infrastructure/fastapi/tests/*`, `src/infrastructure/tests/test_analyze_document_use_case_wiring.py`, `test_export_report_wiring.py`, `test_warm_up_language_model_use_case_wiring.py`.
- Precedent for runner-agnostic preparation: `tests/__init__.py` injects the `win32com` mocks at package import time.
- During TASK-04 verification, a sqlite3 guard blocking access to the real database diagnosed an import-order root cause: under `unittest discover`, `src/infrastructure/fastapi/__init__.py` re-exported `app` and `create_app` from `fastapi_app`, which imported `dependencies.py` where real wirings were built at import time. Because Python imports parent packages before child test packages (`src.infrastructure.fastapi` before `src.infrastructure.fastapi.tests`), the isolation hook in `tests/__init__.py` ran too late. In addition, `test_apply_does_not_create_database_file` in `test_isolated_test_environment.py` was order-dependent on shared temporary state created by earlier wiring tests.
- In TASK-05 Round 2, `unittest discover` walks and imports every package directory encountered even when a `-p` pattern filters test modules. Because `src/infrastructure/fastapi/src/routes` is walked before `src/infrastructure/fastapi/tests`, `routes/__init__.py` imported `analyze_endpoint.py`, which imported `dependencies.py`. Removing the eager re-export in `fastapi/__init__.py` was insufficient because `dependencies.py` eagerly instantiated five wiring singletons at module level (`AnalyzeDocumentUseCaseWiring().create_use_case()`, etc.), opening a connection to the real database and initializing SQLite schema.
- The previous round reported that the database was untouched based on row counts, but the mtime of `data/metrics.db-wal` had changed from 1791230174 to 1791230976 (2026-10-05 17:09:36), proving the database file had been opened.

## 3. Design

- One helper, `IsolatedTestEnvironment` (`src/infrastructure/tests/isolated_test_environment.py`, one class per file, name without the `test_` prefix so discovery ignores it): `apply()` creates a single temporary directory per process (lazily, `TemporaryDirectory(ignore_cleanup_errors=True)`, kept alive for the whole process) and sets, UNCONDITIONALLY (not `setdefault`, because `load_dotenv()` may already have injected the real values): `METRICS_DATABASE_PATH` and `LOG_FILE_PATH` inside it, `USE_EXTERNAL_LLM=false`, `TESTING=True`. It is idempotent.
- The helper is applied at package import time by every test package that can reach the real wiring: `src/infrastructure/tests/__init__.py`, `src/infrastructure/fastapi/tests/__init__.py` and `tests/__init__.py`. `conftest.py` calls the same helper and drops its duplicated inline block, so `pytest` and `unittest` run under the same environment.
- Package `src/infrastructure/fastapi/__init__.py` is stripped of eager re-exports (`app`, `create_app`) and reduced to its docstring to make importing `src.infrastructure.fastapi` free of side effects. All consumers (`web_main.py` and test modules) import `src.infrastructure.fastapi.fastapi_app` directly.
- The five wiring-built singletons in `src/infrastructure/fastapi/src/config/dependencies.py` are lazy: `_analyze_use_case`, `_export_use_case`, `_json_export_use_case`, `_analysis_cancellation_port`, and `_warm_up_language_model_use_case` are initialized to `None`, and each getter (`get_...()`) creates and caches the instance on first access. `_env_config` and `_templates` remain eager (cheap and side-effect free).
- A public function `initialize_dependencies() -> None` in `dependencies.py` eagerly constructs all five singletons on demand.
- `web_main.py:main()` calls `initialize_dependencies()` as its first statement to preserve fail-fast startup behavior at the production entry point without import-time side effects.
- `reset_dependencies()` sets the five lazy singletons back to `None` and recreates `_env_config` and `_templates`, preserving instance refresh and template globals across tests.
- `src/domain/tests` and `src/application/tests` do NOT import it (domain tests must stay pure; application tests use fakes).
- Out of scope: changing the `.env` files, deleting the backup of the cleaned database.

## 4. Tasks

- [x] **TASK-01: Helper and invariant tests** (RED first)
  - **Scope**: `src/infrastructure/tests/isolated_test_environment.py`, `src/infrastructure/tests/test_isolated_test_environment.py`.
  - **Outcome**: Implemented `IsolatedTestEnvironment` in `src/infrastructure/tests/isolated_test_environment.py` with idempotent lazy `TemporaryDirectory` and unconditional environment overrides. Tested via `test_isolated_test_environment.py` (5 tests passing).
- [x] **TASK-02: Apply it in every test package that reaches the wiring**
  - **Scope**: the three `__init__.py` above, one small invariant test per hooked package (`test_environment_isolation.py` in `src/infrastructure/fastapi/tests/` and in `tests/`), `conftest.py`.
  - **Outcome**: Hooked `IsolatedTestEnvironment.apply()` into `src/infrastructure/tests/__init__.py`, `src/infrastructure/fastapi/tests/__init__.py`, `tests/__init__.py`, and simplified `conftest.py`. Verified with package invariant tests across `src` and `tests` (all passing under `unittest discover`).
- [x] **TASK-03: Docs**
  - **Scope**: any doc that tells to export `USE_EXTERNAL_LLM` or `METRICS_DATABASE_PATH` before running the tests (`README.md`, `docs/`, `odd/` runner lines are historical and stay as they are).
  - **Outcome**: Audited `README.md`, `docs/`, and `openspec/`; none instruct exporting `USE_EXTERNAL_LLM` or `METRICS_DATABASE_PATH` for test execution, so no doc updates were required.
- [x] **TASK-04: Verification** (stopped by its own safety protocol, findings fixed in TASK-05)
- [x] **TASK-05: Fix the two defects found by the verification (Rounds 1 and 2)**
  - **Scope**: `src/infrastructure/fastapi/__init__.py`, `src/infrastructure/fastapi/src/config/dependencies.py`, `web_main.py`, `src/infrastructure/fastapi/tests/*`, `src/infrastructure/tests/*`, `tests/*`, `conftest.py`, `odd/tasks/test-database-isolation.md`.
  - **Outcome**:
    - Round 1: Reduced `src/infrastructure/fastapi/__init__.py` to docstring to eliminate import side effects, rewrote `test_apply_does_not_create_database_file` using `patch.object` on `_temporary_directory` to eliminate test order dependence.
    - Round 2: Made the five wiring-built singletons in `dependencies.py` lazy (`None` default, initialized on first getter call) and added `initialize_dependencies()`. Called `initialize_dependencies()` at startup in `web_main.py:main()`. Extended `test_package_import_side_effects.py` with subprocess tests verifying importing `routes` and `fastapi_app` does not create the metrics database. Added lazy-loading unit tests in `test_dependencies.py`. Adapted `tests/test_web_main.py` and `src/infrastructure/tests/test_web_main_logging.py` to patch `initialize_dependencies` and verified call ordering before `uvicorn.run`.
- [x] **TASK-06: Re-verification** (approved by the user and run by gentle-ai-verify on 2026-10-05, stop-on-first-change protocol: sqlite guard runs `src` 1543 and `tests` 51 with 0 real-database attempts; plain `unittest` `src` 1543 OK and `tests` 51 OK with NO environment overrides; `pytest` 1594 passed; ruff/pyright clean except 3 diagnostics of `tests/__init__.py` that already exist in HEAD; `data/metrics.db` rows 34 / 138 / 296, `-wal` and `silvina.log` mtimes, reports folder (25 entries) and process lists identical before and after every run)
