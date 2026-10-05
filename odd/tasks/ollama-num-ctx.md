# Feature: Configurable Ollama Context Size (`OLLAMA_NUM_CTX`)

- **Feature Name**: `ollama-num-ctx`
- **File Locator**: `odd/tasks/ollama-num-ctx.md`
- **Branch**: `feat/configurable-text-limits` (the user's working branch for the full-article analysis changes; follows `bce74c7`)
- **TDD Mode**: Test-first for every behavior change (RED then GREEN)
- **TDD Runner**: `export USE_EXTERNAL_LLM=false APP_MODE=PROD; .venv/Scripts/python.exe -m unittest discover -s src -t . -p "test_*.py"` and the same with `-s tests` (do NOT invoke a test module directly)
- **Commit policy**: no commit until the user orders it; one task at a time, wait for the user's approval before the next task or the verifier
- **Edit-tool restriction**: the agent cannot edit `.env` or `.env.example`; the user adds the lines listed in TASK-05 by hand

---

## 1. Objective

Let the deployment choose the Ollama context window (`num_ctx`). Today the application never sends it, so Ollama applies its VRAM-based default of 4,096 tokens (measured in `logs/ollama.log`: `default_num_ctx=4096`, `n_ctx_slot = 4096`). Any prompt above that is truncated silently. This is a prerequisite for sending the full article (about 30,000 characters, an estimated 9-10k tokens per call) to the model.

## 2. Decisions

- New variable `OLLAMA_NUM_CTX`. Absent or empty means "do not send `num_ctx`": Ollama keeps deciding, so behavior is identical to today. A set value must be a positive integer; anything else fails fast in `EnvConfig` (like `OLLAMA_MODEL_KEEP_ALIVE`).
- The value is an Ollama infrastructure detail: it is injected into the Ollama adapters only. The domain options (`temperature`, `num_predict`) and the Claude adapter do not change.
- The warm-up MUST load the model with the same `num_ctx` as the real calls. Ollama reloads the model when the runner parameters change (60-76 s), so a mismatch would waste the warm-up (see `odd/tasks/ollama-warmup-keepalive.md`).
- Recommended value for 30-40k character articles: `16384`. A client using another `num_ctx` on the same Ollama (another application loaded this model at 32,768 on 2026-10-01) forces reloads between the two.
- Out of scope: sending the full article to the model, prompt changes, KV-cache or flash-attention settings, any server-side Ollama configuration.

## 3. Design

- `EnvConfig.ollama_num_ctx: int | None`.
- `OllamaGeneratorAdapter(model_name, base_url, think, keep_alive, num_ctx, error_mapper)`: when `num_ctx` is not `None`, every `generate` call sends `options = {**(options or {}), "num_ctx": num_ctx}`; when it is `None` the call is identical to today (options passed through untouched, including `None`).
- `OllamaLanguageModelWarmupAdapter(model_name, base_url, keep_alive, num_ctx, error_mapper)`: when `num_ctx` is not `None`, the empty-prompt call also sends `options={"num_ctx": num_ctx}`; when it is `None` the call is identical to today.
- Wirings: `AnalyzeDocumentUseCaseWiring._get_ollama_generator` and `WarmUpLanguageModelUseCaseWiring._language_model_warmup_port` pass `env_config.ollama_num_ctx`.

## 4. Tasks

- [x] **TASK-01: Configuration**
  - **Scope**: `src/infrastructure/env_config.py`, `src/infrastructure/tests/test_env_config.py`.
  - **Outcome**: Added `EnvConfig.ollama_num_ctx: int | None` attribute parsed via private `_parse_ollama_num_ctx()` helper. Unset or blank returns `None`; valid numbers parse as positive integers; zero, negative values, and non-numeric values raise `ValueError` matching `_parse_ollama_keep_alive` style.
- [x] **TASK-02: Generator adapter**
  - **Scope**: `src/infrastructure/adapters/llm_generator/ollama_generator_adapter.py`, `src/infrastructure/tests/test_ollama_generator_adapter.py`.
  - **Outcome**: Added required `num_ctx: int | None` constructor parameter after `keep_alive` and before `error_mapper`. In `generate_with_usage`, when `num_ctx` is set, merges `{**(options or {}), "num_ctx": num_ctx}` without mutating caller dict; when `None`, preserves original `options` passthrough unmodified. Updated test doubles and added test coverage.
- [x] **TASK-03: Warm-up adapter**
  - **Scope**: `src/infrastructure/adapters/llm_generator/ollama_language_model_warmup_adapter.py`, `src/infrastructure/tests/test_ollama_language_model_warmup_adapter.py`.
  - **Outcome**: Added required `num_ctx: int | None` constructor parameter after `keep_alive` and before `error_mapper`. In `warm_up`, sends `options={"num_ctx": num_ctx}` only when set; when `None`, call omits the `options` keyword matching prior behavior. Updated test doubles and added test coverage.
- [x] **TASK-04: Wiring**
  - **Scope**: `src/infrastructure/wirings/analyze_document_use_case_wiring.py`, `src/infrastructure/wirings/warm_up_language_model_use_case_wiring.py`, their tests.
  - **Outcome**: Injected `num_ctx=env_config.ollama_num_ctx` into `AnalyzeDocumentUseCaseWiring._get_ollama_generator` and `WarmUpLanguageModelUseCaseWiring._language_model_warmup_port`. Added wiring tests asserting absent default (`None`) and environment variable override.
- [x] **TASK-05: Documentation and configuration**
  - **Scope**: `openspec/specs/**` where Ollama configuration is described. Lines for `.env` and `.env.example` (added by the user by hand): `OLLAMA_NUM_CTX=16384` in the Ollama connection section.
  - **Outcome**: Updated `openspec/specs/analyze-document/spec.md` with `OLLAMA_NUM_CTX` attribute table row and validation rules, and updated `openspec/specs/classify-article/spec.md` with `OllamaGeneratorAdapter` `num_ctx` options merge behavior and scenarios. `.env` and `.env.example` left untouched per safety policy for manual addition.
- [x] **TASK-06: Verification** (approved by the user and run by gentle-ai-verify on 2026-10-05: `src` 1529 tests OK, `tests` 49 OK, ruff clean, pyright 0 errors, structural greps clean, behavior parity confirmed with `ollama.Client` mocked; `.env` has `OLLAMA_NUM_CTX=16384`, `.env.example:26` too)
  - **Scope**: full `src` and `tests` suites, ruff, pyright, defaults parity (variable absent means no `num_ctx` is sent).
