# Feature: CLI Language Model Warm-up

- **Feature Name**: `cli-model-warm-up`
- **File Locator**: `odd/tasks/cli-model-warm-up.md`
- **Branch**: `feat/cli-model-warm-up` (from `silvina_editorial_v100`)
- **TDD Mode**: Enabled (RED -> GREEN -> REFACTOR) where a runnable test applies
- **TDD Runner**: `.venv/Scripts/python -m unittest discover -s src -t . -p "test_*.py"` with `USE_EXTERNAL_LLM=false APP_MODE=PROD`
- **Delivery Strategy**: stop before every commit and wait for the user's instructions

---

## 1. Objective

When the command line analysis uses a local Ollama model, preload the model before analyzing, as the web does on startup. A real run of `main.py` over `01_IMRyD_Gomez_Rubio.docx` with `--use-external-llm false` failed with "The language model backend is unavailable." on the first request.

## 2. Agreed specification

- The CLI runs the existing `WarmUpLanguageModelUseCase` as its own announced step, "Precargando el modelo de lenguaje", right before "Analizando el documento".
- The warm-up uses the same overrides as the analysis (`--ollama-model-name`, `--use-external-llm`, `--llm-provider`, `--app-mode`). It is a no-op for an external provider or when `OLLAMA_WARMUP_ON_STARTUP` is false, exactly as in the web.
- Unlike the web (background thread, failure only logged), the CLI waits for the warm-up and a language model error stops the run with the same clean message and exit status the analysis step already gives.

- Phase 2 (user request): when the provider is a local Ollama and its server does not respond, the CLI starts the system `ollama serve` itself, waits until it answers (time limit), then continues. Superseded by phase 3: the server the CLI started is closed after 5 minutes without use (see below). Stopping only `ollama.exe` leaves GPU-holding orphans (finding F-12 of `odd/tasks/real-run-findings.md`), so the whole process tree is terminated.
- The server check is announced as its own step, "Verificando el servidor del modelo de lenguaje", before the warm-up step. It is independent of `OLLAMA_WARMUP_ON_STARTUP`, because the analysis needs the server anyway. It is a no-op for an external provider. It only starts a server for a local `OLLAMA_BASE_URL` (localhost, 127.0.0.1, ::1); for a remote host it fails with the clean message. If the `ollama` executable is not found, or the server does not answer in time, the run stops with status 1 and a clean message.

- Phase 3 (user request): a server started by the CLI is closed after 5 minutes without use, so it is not left on without use. Scope decided by the user: ONLY a server started by the CLI; a server that was already running (tray application, web, other tools) is never touched.
- The CLI ends right after the analysis, so a detached watcher process closes the server. Shared state is a lease file (`data/ollama_server_lease.json`, git-ignored) with the server process id, the process id of the CLI run using it (or none) and the time of the last use. Every CLI run that finds a leased server alive marks it in use at the start and idle at the end (success, failure or interruption), so a second run within the 5 minutes restarts the count. The watcher never counts idleness while the CLI process that holds the lease is alive (a slow analysis is never cut), and exits without killing anything when the lease is gone, superseded, or the server already stopped.

## 3. Constraints

- `WarmUpLanguageModelUseCaseWiring` reads `EnvConfig()` without overrides, so it cannot be reused as is. New subclass `OverridableWarmUpLanguageModelUseCaseWiring` overrides only `_env_config()` with `OverridableEnvConfig`, mirroring `OverridableAnalyzeDocumentUseCaseWiring`. The web wiring is not modified.
- The existing test `test_does_not_call_warm_up...` in `test_cli_analysis_services_wiring.py` (asserts the warm-up factory is never called) encoded the previous decision and is replaced.

## 4. Tasks

- [x] **TASK-01** `OverridableWarmUpLanguageModelUseCaseWiring` (new file, overrides applied to the warm-up). RED first.
- [x] **TASK-02** `CliAnalysisServices` gets `warm_up_language_model_use_case`; `CliAnalysisServicesWiring` builds it with the overrides. Replace the old "never called" test. RED first.
- [x] **TASK-03** `DocumentAnalysisCommand` runs the warm-up step before the analysis and stops with a clean error when it fails; e2e and README updated.

- [x] **TASK-04** Start the system Ollama server when it is not running: domain port `LanguageModelServerPort` and service `LanguageModelServerStarter`, error `LanguageModelServerStartFailed`, use case `EnsureLanguageModelServerUseCase`, adapters `OllamaServerAdapter` and `NoOpLanguageModelServerAdapter`, wiring, new CLI step. RED first.

- [x] **TASK-05** Idle shutdown of the server started by the CLI (lease file, detached watcher, process tree termination, release step in the command). RED first.

- [x] **TASK-06** Three user findings from real use: (1) with an external model the steps "Verificando el servidor del modelo de lenguaje" and "Precargando el modelo de lenguaje" must not be shown (also skip the warm-up step when `OLLAMA_WARMUP_ON_STARTUP=false`); (2) with the local model many console windows open and close and one stays: the server and the watcher are launched with `DETACHED_PROCESS`, so every console child (the watcher's `tasklist`, Ollama runners) opens its own window; use `CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP` instead, and pass `CREATE_NO_WINDOW` to the `tasklist`/`taskkill` calls; (3) the 5 minutes become the REQUIRED `.env` setting `OLLAMA_SERVER_IDLE_SHUTDOWN` with a unit (`5m`, `90s`, `1h`), failing fast when missing, blank or invalid (user decision: not optional, so nothing breaks silently).

## 5. Open items

- Resolved by TASK-04: a stopped Ollama server is started by the CLI instead of failing.

## 6. Evidence

### TDD Execution
- **TASK-01 RED**: `ModuleNotFoundError: No module named 'src.infrastructure.wirings.overridable_warm_up_language_model_use_case_wiring'` on running `test_overridable_warm_up_language_model_use_case_wiring.py`.
- **TASK-01 GREEN**: 6 unit tests passing in `test_overridable_warm_up_language_model_use_case_wiring.py`.
- **TASK-02 RED**: `AttributeError: 'CliAnalysisServices' object has no attribute 'warm_up_language_model_use_case'` and missing wiring in `test_cli_analysis_services_wiring.py` (3 errors).
- **TASK-02 GREEN**: 10 unit tests passing in `test_cli_analysis_services_wiring.py`.
- **TASK-03 RED**: `AssertionError: Expected 'execute' to be called once. Called 0 times` and step assertion mismatch in `test_document_analysis_command.py` (5 failures).
- **TASK-03 GREEN**: 26 unit tests passing in `test_document_analysis_command.py`.
- **TASK-04 RED**: `ImportError` on missing `LanguageModelServerStartFailed`; `ModuleNotFoundError` on missing `LanguageModelServerStarter`, `EnsureLanguageModelServerUseCase`, `NoOpLanguageModelServerAdapter`, `OllamaServerAdapter`, `EnsureLanguageModelServerUseCaseWiring`; `AttributeError` on missing `ensure_language_model_server_use_case` in `CliAnalysisServices`; 3 failures in `test_document_analysis_command.py` (missing server execution, error reporting, step announcement mismatch).
- **TASK-04 GREEN**: 5 tests in `test_language_model_server_start_failed.py`, 6 in `test_language_model_server_starter.py`, 3 in `test_ensure_language_model_server_use_case.py`, 3 in `test_noop_language_model_server_adapter.py`, 15 in `test_ollama_server_adapter.py`, 5 in `test_ensure_language_model_server_use_case_wiring.py`, 12 in `test_cli_analysis_services_wiring.py`, 28 in `test_document_analysis_command.py`.
- **TASK-05 RED**: `AttributeError` for missing `mark_in_use_call_count` and `release` in domain starter/fake port; `ModuleNotFoundError` for missing `ReleaseLanguageModelServerUseCase`, `OllamaServerLease`, `OllamaServerLeaseStore`, `ProcessInspector`, `ProcessTreeTerminator`, `OllamaIdleShutdownWatcher`, `ReleaseLanguageModelServerUseCaseWiring`, `OllamaIdleShutdownWatcherWiring`, `ollama_idle_shutdown_watcher_main`; `TypeError` for unimplemented abstract methods `mark_in_use` and `mark_idle` on `OllamaServerAdapter`; `AttributeError` for missing `release_language_model_server_use_case` on `CliAnalysisServices`; 6 test failures in `test_document_analysis_command.py` for uncalled release execution.
- **TASK-05 GREEN**: 9 unit tests passing in `test_language_model_server_starter.py`, 2 in `test_release_language_model_server_use_case.py`, 5 in `test_noop_language_model_server_adapter.py`, 10 in `test_ollama_server_lease_store.py`, 7 in `test_process_inspector.py`, 4 in `test_process_tree_terminator.py`, 9 in `test_ollama_idle_shutdown_watcher.py`, 26 in `test_ollama_server_adapter.py`, 4 in `test_release_language_model_server_use_case_wiring.py`, 1 in `test_ollama_idle_shutdown_watcher_wiring.py`, 1 in `test_ollama_idle_shutdown_watcher_main.py`, 14 in `test_cli_analysis_services_wiring.py`, 35 in `test_document_analysis_command.py`.
- **TASK-05 Real-Run Bug Fix**: In real runs, `OllamaServerAdapter.start()` spawns the watcher while `ollama serve` takes ~20 s to answer HTTP requests. The watcher's first poll previously checked `server_port.is_running()`, got `False`, cleared the lease, and exited prematurely. Fixed by checking process liveness via `not process_inspector.is_alive(server_process_id)` instead of server HTTP responsiveness; removed unused `server_port` and `--base-url` dependencies from the watcher, wiring, and launcher. RED: `TypeError` on watcher initialization without `server_port` and failure on dead process clearing without termination; GREEN: 9 unit tests passing in `test_ollama_idle_shutdown_watcher.py`.
- **TASK-05 Stale PATH Executable Lookup Bug Fix**: When the terminal was opened prior to adding Ollama to PATH, `shutil.which("ollama")` failed even though Ollama was installed. Implemented `OllamaExecutableLocator` checking process PATH, then persistent Windows registry PATH (HKCU `Environment` and HKLM `SYSTEM\CurrentControlSet\Control\Session Manager\Environment`), then `%LOCALAPPDATA%\Programs\Ollama`. Added `LanguageModelServerExecutableNotFound(LanguageModelServerStartFailed)` with an informative message. RED: `ImportError` for missing exception class and `ModuleNotFoundError` for missing locator; GREEN: 4 tests in `test_language_model_server_executable_not_found.py`, 9 in `test_ollama_executable_locator.py`, and 27 in `test_ollama_server_adapter.py`.
- **TASK-06 RED**:
  Part A: `AttributeError` for missing `uses_local_language_model` and `warms_up_language_model` in `OverridableAnalyzeDocumentUseCaseWiring` and `CliAnalysisServices`; `AssertionError` in `test_document_analysis_command.py` for executing/announcing server check and warm-up with external model or disabled warm-up.
  Part B: `AssertionError: expected call not found` in `test_process_inspector.py`, `test_process_tree_terminator.py`, and `test_ollama_server_adapter.py` expecting `CREATE_NO_WINDOW` and `CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW` flags instead of `DETACHED_PROCESS`.
  Part C: `AssertionError` in `test_complete_test_environment.py` for missing `OLLAMA_SERVER_IDLE_SHUTDOWN`, `AttributeError` in `EnvConfig` for missing `ollama_server_idle_shutdown_seconds`, and `SettingValueMissing`/`ValueError` failures in `test_env_config.py`.
- **TASK-06 GREEN**:
  Part A: 20 unit tests in `test_overridable_analyze_document_use_case_wiring.py`, 17 in `test_cli_analysis_services_wiring.py`, 38 in `test_document_analysis_command.py`.
  Part B: 7 unit tests in `test_process_inspector.py`, 4 in `test_process_tree_terminator.py`, 27 in `test_ollama_server_adapter.py`.
  Part C: 2 unit tests in `test_complete_test_environment.py`, 96 in `test_env_config.py`, 32 in `test_overridable_env_config.py`, 11 in `test_ensure_language_model_server_use_case_wiring.py`, 4 in `test_release_language_model_server_use_case_wiring.py`.

### Validation
- Full test suite: `USE_EXTERNAL_LLM=false APP_MODE=PROD .venv/Scripts/python -m unittest discover -s src -t . -p "test_*.py"` -> 2171 tests passing.
- CLI argument tests and E2E: `.venv/Scripts/python -m unittest tests/test_main_cli_args.py tests/e2e/test_cli_e2e.py` -> 11 tests passing.
- Linter and formatting: `.venv/Scripts/python -m ruff check` and `ruff format --check` clean on all touched files and repo.
