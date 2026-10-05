# Feature: Ollama Model Warm-up at Server Start and keep_alive

- **Feature Name**: `ollama-warmup-keepalive`
- **File Locator**: `odd/tasks/ollama-warmup-keepalive.md`
- **Branch**: `feat/ollama-warmup-keepalive` (from `silvina_editorial_v100` at `6816643`; independent of `feat/ollama-official-model`)
- **TDD Mode**: Test-first for every behavior change (RED then GREEN); the real-model measurement is functional verification
- **TDD Runner**: `export USE_EXTERNAL_LLM=false APP_MODE=PROD; .venv/Scripts/python.exe -m unittest discover -s src -t . -p "test_*.py"` and the same with `-s tests` (the repo `.env` points to Claude, hence the overrides; do NOT invoke a test module directly, it gives false `METRICS_DATABASE_PATH` errors)
- **Delivery Strategy**: `ask-on-risk`
- **Commit policy**: one work-unit commit per group of tasks, Conventional Commits, final `docs(odd)` commit; push, PR and merge only on the user's express order
- **Edit-tool restriction**: the Gentle AI safety policy blocks writing `.env.example`; that file is edited by the user by hand

---

## 1. Objective

Remove the cold start of the Ollama model from the first analysis of a session.

Measured evidence (`data/metrics.db`, Ollama runs, and `server.log` of 2026-10-02): the first `/api/generate` after idle takes about 60 s (model load of 14 GB), later calls take 6 to 9 s; `classify_article` averages 77 s with 15 output tokens (0.2 tok/s) and has a minimum of 6.5 s; Engram #2508 measured a 76 s load. Ollama unloads the model after `OLLAMA_KEEP_ALIVE` (5 min default).

## 2. Decisions taken by the user (2026-10-04)

- The warm-up happens when the SERVER starts (FastAPI lifespan), not when the page is opened and not when a file is chosen. It runs in a background daemon thread, next to the thread that opens the browser, and never blocks the app.
- It is active only when Ollama is the effective provider. The user stated the rule as `USE_EXTERNAL_LLM=false`; the implementation conditions it on `llm_provider is AiProvider.OLLAMA`, which covers that case and also `APP_MODE=PROD` with `USE_EXTERNAL_LLM=true` (the flag is ignored there and Ollama is used). One-line change if a literal reading is preferred.
- `keep_alive` default: 15 minutes (the model holds 14 of 16 GB of VRAM and the same GPU is used for OpenArma/Arma; see Engram #2508).
- Out of scope: the CLI (`main.py`) does not warm up; warming when a file is chosen; any change to prompts or model.

## 3. Design

- `EnvConfig`: `ollama_model_keep_alive: str` from `OLLAMA_MODEL_KEEP_ALIVE` (default `15m`; fail fast on an invalid value: an integer number of seconds or Go-style durations such as `15m`, `1h30m`, `-1`; the name avoids `OLLAMA_KEEP_ALIVE`, which is the Ollama SERVER variable) and `ollama_warmup_on_startup: bool` from `OLLAMA_WARMUP_ON_STARTUP` (default `true`, strict `true`/`false` like the other booleans).
- `OllamaGeneratorAdapter(model_name, base_url, think, keep_alive)` (no default, constructor injection like `think`) passes `keep_alive` on every `generate`. The backend exception mapping is extracted to a small collaborator reused by the warm-up adapter (behavior-preserving; the existing tests are the safety net).
- Domain, folder `src/domain/language_model/` (matches the existing `language_model_errors.py` grouping): port `LanguageModelWarmupPort` (`warm_up() -> None`) and domain service `LanguageModelWarmer` (delegates to the port, measures and logs the duration).
- Application: `WarmUpLanguageModelUseCase.execute()` decorated with `@generic_error_handler`.
- Infrastructure: `OllamaLanguageModelWarmupAdapter(model_name, base_url, keep_alive)` sends `client.generate(model=..., prompt="", keep_alive=...)` (an empty prompt loads the model without generating) and maps backend errors to the existing `LanguageModel*` errors (a missing model becomes `LanguageModelNotFound`, useful in the warning log); `NoOpLanguageModelWarmupAdapter` for the other cases. The wiring `WarmUpLanguageModelUseCaseWiring` picks the real adapter only when `llm_provider is OLLAMA` and `ollama_warmup_on_startup` is true, so no conditionals leak into the lifespan.
- FastAPI: singleton in `dependencies.py`; `create_app(auto_open_browser=True, warm_up_language_model=True)` stores the flag in `app.state`; the lifespan starts the daemon thread when it is true and `TESTING` is not set; any `BaseSrcError` or `Exception` in the thread is logged as a warning, never raised. The 6 existing test call sites of `create_app` pass `warm_up_language_model=False` so tests never reach a real Ollama.
- Risk to check in the real measurement: the model must not be reloaded by the first real request (the warm-up must load with the same runner parameters; the real calls send only `temperature` and `num_predict`, no `num_ctx`). Verify with `ollama ps` and the server log.

## 4. Tasks

- [x] **TASK-01: Configuration**
  - **Scope**: `src/infrastructure/env_config.py`, `src/infrastructure/tests/test_env_config.py`, `openspec/specs/analyze-document/spec.md` (variable table).
  - **Verification**: RED then GREEN: defaults (`15m`, `true`), valid and invalid durations, strict boolean.
- [x] **TASK-02: keep_alive in the generator adapter and shared error mapping**
  - **Scope**: `src/infrastructure/adapters/llm_generator/ollama_generator_adapter.py`, new `ollama_backend_error_mapper.py` in the same folder, `src/infrastructure/wirings/analyze_document_use_case_wiring.py`, tests of the adapter, the mapper and the wiring.
  - **Verification**: RED then GREEN: `generate` forwards `keep_alive`; mapper tests equal to the previous mapping behavior; the wiring injects `env_config.ollama_model_keep_alive`.
  - **Commit 1**: `feat(llm): send keep_alive on every Ollama request` (`b67e3aa`)
- [x] **TASK-03: Domain and application**
  - **Scope**: `src/domain/language_model/language_model_warmup_port.py`, `language_model_warmer.py`, `src/application/warm_up_language_model_use_case.py` and their tests (`src/domain/tests/language_model/`, `src/application/tests/`).
  - **Verification**: RED then GREEN with a fake port (delegates once, logs the duration, the use case propagates domain errors and wraps unexpected ones).
- [x] **TASK-04: Adapters and wiring**
  - **Scope**: `src/infrastructure/adapters/llm_generator/ollama_language_model_warmup_adapter.py`, `noop_language_model_warmup_adapter.py`, `src/infrastructure/wirings/warm_up_language_model_use_case_wiring.py`, test double wiring if needed, and tests.
  - **Verification**: RED then GREEN: the adapter sends an empty prompt with `keep_alive` and maps `ResponseError` 404 to `LanguageModelNotFound`; the wiring returns the real adapter only for Ollama with the flag on.
  - **Commit 2**: `feat(llm): add the language model warm-up use case and its Ollama adapter` (`1099ba4`)
- [x] **TASK-05: FastAPI lifespan**
  - **Scope**: `src/infrastructure/fastapi/fastapi_app.py`, `src/infrastructure/fastapi/src/config/dependencies.py`, the 6 test call sites of `create_app`, new lifespan tests.
  - **Verification**: RED then GREEN: the lifespan starts one daemon thread when enabled, none when `warm_up_language_model=False` or `TESTING` is set, a failing warm-up only logs a warning and the app still starts.
  - **Commit 3**: `feat(fastapi): warm up the language model when the server starts` (`b0e6599`)
- [x] **TASK-06: Real measurement (authorized by the user on 2026-10-04)**
  - **Verification**: with the real `gemma4-26b-adapted` and a scratch metrics database: start `web_main.py`, `ollama ps` shows the model loaded without any request, one analysis, `classify_article` close to 6 to 9 s, no reload in the server log; stop Ollama with `taskkill //F //T //PID` and confirm no `llama-server.exe` remains (Engram #2508).
- [x] **TASK-07: Documentation**
  - **Scope**: `README.md` (what the warm-up does, the two variables, the VRAM trade-off), spec table if not done in TASK-01. `.env.example` is left for the user.
  - **Commit 4**: `docs(config): document the Ollama warm-up and keep_alive variables`

## 5. Excluded on purpose

1. Warming up when a file is chosen (a later iteration if needed).
2. Warm-up in the CLI.
3. Parallelizing the LLM calls (`OLLAMA_NUM_PARALLEL=1` and about 2 GB of VRAM headroom make it useless here).

## 6. Evidence log

### TASK-01 / TASK-02 (2026-10-04)

- RED then GREEN for each behavior (defaults, accepted and rejected durations, boolean parsing; `keep_alive` forwarded to `generate`; mapper equal to the previous mapping; wiring injects `keep_alive`). Full `src` suite: 1437 tests OK (baseline 1420).
- Review of the worker's code: `from re import compile` shadowed the builtin; replaced by `fullmatch` with an unanchored pattern; behavior checked with 12 sample values (the trailing-newline value `15m
` is rejected).

### TASK-03 / TASK-04 / TASK-05 (2026-10-04)

- RED then GREEN per class (warmer, use case, Ollama adapter, no-op adapter, wiring, lifespan). `src`: 1463 tests OK; `tests`: 48 OK. (On `feat/ollama-official-model` the same suite has 49 because that branch adds one banner test.)
- Layer check: `src/domain/language_model` and the use case import nothing from infrastructure. `@generic_error_handler` only on `WarmUpLanguageModelUseCase.execute`.
- The wiring chooses the Ollama adapter only when `llm_provider is AiProvider.OLLAMA` and `ollama_warmup_on_startup`; the four cases are tested (default, flag off, DEBUG with Claude -> no-op, PROD with `USE_EXTERNAL_LLM=true` -> Ollama).
- Tests cannot reach a real Ollama: the 5 test call sites of `create_app` pass `warm_up_language_model=False` (the project runner `unittest discover` does not set `TESTING`, so `TESTING` alone did not protect them).
- Worker extras kept on purpose: the new singleton is also re-created in the existing `reset_dependencies`; one `assert ... is not None` added in `tests/e2e/test_fastapi_e2e.py` for the type checker (not requested, harmless). My own count of call sites ("6") was wrong: there are 5.

### TASK-06 (real measurement, 2026-10-04, authorized by the user)

Setup: the FastAPI app started from a scratch script on port 7871 (`create_app(auto_open_browser=False, warm_up_language_model=True)`), `APP_MODE=PROD`, `USE_EXTERNAL_LLM=false`, `gemma4-26b-adapted`, scratch metrics database, log and reports in a temporary directory (removed afterwards). Baseline: nothing loaded, VRAM 2.17 GB, only `ollama.exe` running.

- **Warm-up without any request**: the model showed in `ollama ps` 68 s after the server start (polled every 5 s); the app log says `Language model warm-up completed in 63.88 seconds`; `ollama ps`: 14 GB, 100 % GPU, `14 minutes from now`, so the 15 minutes `keep_alive` was applied. The server answered HTTP 200 while the model was loading (the warm-up does not block).
- **One real analysis** (`capacidades_razonamiento_emergente_LLMs.docx`): total 111.2 s, HTTP 200. `classify_article` **8.0 s** (15 output tokens, `done_reason` stop) against 60 to 80 s when the model is cold (server.log of 2026-10-02: first call 1m0s; Engram #2557: 79.9 s). The Ollama log kept 1 `model loaded` line before and after the analysis (no reload) and `ollama ps` was unchanged.
- Remaining time is generation, not loading: `analyze_quality` 95.1 s (two quality calls of 35.3 s and 30.3 s, two suitability calls of 13.6 s and 15.8 s).
- Cleanup verified: server stopped by exact PID with `taskkill //F //T`, port 7871 free, `ollama stop`, `ollama ps` empty, no `llama-server.exe`, VRAM back to 2.16 GB, scratch directory deleted.
- Limits: a single run; `ollama ps` shows a context of 4096 (the default, unchanged by this feature); the failure paths of the warm-up (model not installed, Ollama down) are covered by tests but were not exercised against a real Ollama.

### Final verification (gentle-ai-verify, 2026-10-04)

- `src`: 1463 tests OK; `tests`: 48 OK; `ruff check` and `ruff format --check` clean on the 30 Python files changed since `6816643`. No import of infrastructure or ollama in `src/domain` or `src/application` introduced by the branch. No test can reach a real Ollama.
- Residual risk found by the verifier (not fixed): `fastapi_app.py` builds `app = create_app()` with the warm-up enabled by default. Today no test enters the lifespan of that instance (`tests/test_web_main.py` and `test_web_main_logging.py` only compare its identity and mock `uvicorn.run`); a future test that does `with TestClient(app)` without `TESTING` would start a real warm-up.

### Pending for the user

- `.env.example` (blocked for the edit tool): add `OLLAMA_MODEL_KEEP_ALIVE=15m` and `OLLAMA_WARMUP_ON_STARTUP=true` in the Ollama section.
