# Feature: Versioned Settings File (`settings.toml`)

- **Feature Name**: `settings-file`
- **File Locator**: `odd/tasks/settings-file.md`
- **Branch**: `feat/settings-file` (from `silvina_editorial_v100` at `58c78b5`)
- **TDD Mode**: Test-first for every behavior change (RED then GREEN)
- **TDD Runner**: `export USE_EXTERNAL_LLM=false APP_MODE=PROD; .venv/Scripts/python.exe -m unittest discover -s src -t . -p "test_*.py"` and the same with `-s tests` (do NOT invoke a test module directly)
- **Commit policy**: one work-unit commit per group, on this branch. The agent STOPS before every commit and waits for the user's approval.

---

## 1. Objective

The `.env` file mixes deployment values (paths, URLs, mode) with tuning parameters (thresholds, sampling limits, sizes). The tuning parameters are not secrets. Move them to a versioned `settings.toml` read by the program, and keep `.env` for what depends on the machine or is secret.

## 2. Decisions

- Format: TOML, read with the stdlib `tomllib` (no new dependency). Sections per group.
- Location: `settings.toml` at the project root, next to `version.txt`.
- Precedence: environment variable > `settings.toml`. The hardcoded defaults in `EnvConfig` disappear for migrated values: a key missing from both sources fails fast with a message naming the section and key.
- Environment variable names are kept unchanged, so existing overrides and tests keep working.
- `EnvConfig` keeps its public attributes and its no-argument constructor (108 callers). It only gains an optional `settings_file_path` parameter.
- The loader lives in `src/infrastructure/`; `domain/` and `application/` are untouched.
- `.env.example` is left untouched in every group (user decision): it keeps listing the override names.
- Value policy (user decision): `settings.toml` always takes the values currently in the local `.env` (the user authorized reading it), never the code defaults, without asking again. Known differences: `QUALITY_MIN_SAMPLE_WORD_COUNT=10000`, `QUALITY_TEXT_SAMPLE_CHARACTER_LIMIT=32000`, `ARTICLE_CLASSIFICATION_SAMPLE_INTRODUCTION_CHARACTER_LIMIT=32000`.
- Gotcha: a line left in the local `.env` overrides `settings.toml`. The user decided `.env` keeps its parameters; the agent never edits `.env`.
- Stays in `.env` for now (deployment or mode, not tuning): `APP_MODE`, `METRICS_DATABASE_PATH`, `LOG_FILE_PATH`, `LOG_LEVEL`, `LOG_RETENTION_DAYS`, `OLLAMA_BASE_URL`, `USE_EXTERNAL_LLM`, `LLM_PROVIDER`, `EXTERNAL_LLM_MODEL_NAME`, `SILVINA_APP_NAME`.
- Stays in `.env` (user decision 2026-10-06, final): `APP_MODE`, `METRICS_DATABASE_PATH`, `LOG_FILE_PATH`, `LOG_LEVEL`, `LOG_RETENTION_DAYS`, `OLLAMA_MODEL_NAME`, `OLLAMA_BASE_URL`, `OLLAMA_THINK`, `OLLAMA_MODEL_KEEP_ALIVE`, `OLLAMA_WARMUP_ON_STARTUP`, `OLLAMA_NUM_CTX`, `USE_EXTERNAL_LLM`, `LLM_PROVIDER`, `EXTERNAL_LLM_MODEL_NAME` and `EXTERNAL_LLM_THINK`. A first TASK-07 that migrated four of them was cancelled (see below).

## 3. Tasks

- [x] **TASK-01: Loader, mechanism and group `grammar` / `structure` / `citation`**
  - **Scope**: `src/domain/exceptions/settings_errors.py`, `src/infrastructure/settings_file_loader.py`, `src/infrastructure/settings_value_resolver.py`, `src/infrastructure/env_config.py`, `settings.toml`, tests.
  - **Errors (user decision)**: the new code raises domain exceptions, not standard ones: `SettingsError(BaseSrcError)` with `SettingsFileNotFound`, `SettingsFileInvalid`, `SettingValueMissing`, `SettingValueInvalid`. Following the `SrcGenericError` precedent, each has a fixed `MESSAGE` plus a `detail` constructor argument (file path, section, key, variable) so the error stays actionable; `dict()` and `str()` return `MESSAGE` followed by the detail. Pre-existing `ValueError`s in `EnvConfig` parsers (`OLLAMA_*`, booleans, required variables) are untouched.
  - **Outcome**: `SettingsFileLoader` (TOML via `tomllib`, fail-fast on missing or malformed file) and `SettingsValueResolver` (env var > file, typed `read_integer`/`read_float`/`read_string`, errors naming section, key and env var). `EnvConfig(settings_file_path=...)` now reads the six grammar/structure/citation values through them; `settings.toml` created with `[grammar]`, `[structure]`, `[citation]`; their values equal the ones in the local `.env` (checked 2026-10-05). Verified by gentle-ai-verify: `src` 1594 OK (re-run after the domain-exception change), `tests` 51 OK, ruff clean. Pyright is not installed in `.venv`, so typing is unverified.
  - **User decision (2026-10-05)**: `.env.example` keeps every migrated key (it documents the environment override names); the agent does not remove lines from it in any task. Only a stale line in the local `.env` matters, because it overrides `settings.toml`.
  - **User decision (2026-10-05)**: the local `.env` keeps its parameters too; the agent never edits `.env` and does not ask the user to delete lines. Consequence: while a key is present in `.env`, it overrides `settings.toml`, so editing that key in `settings.toml` has no effect on this machine.
  - **Commit**: `fe22718` `feat(config): read grammar, structure and citation settings from settings.toml`.
- [x] **TASK-02: Group `article_classifier` / `article_classification` / `article_size`**
  - **Scope**: `settings.toml`, `src/infrastructure/env_config.py`, `src/infrastructure/tests/test_env_config_settings_file.py`, `src/infrastructure/tests/test_env_config.py`.
  - **Outcome**: 12 values (2 classifier, 4 classification sampling, 6 size bands) read from `[article_classifier]`, `[article_classification]`, `[article_size]`. User decision: `sample_introduction_character_limit = 32000` (the value in use in `.env`), not the old default 3500; the two assertions in `test_env_config.py` and the one in `test_analyze_document_use_case_wiring.py` that expected 3500 now expect 32000 (the wiring one was found by the first verifier run). Verified by gentle-ai-verify: `src` 1597 OK, `tests` 51 OK, ruff clean. Native review (1 lens, medium risk) approved and acknowledged.
  - **Commit**: `694ac4c` `feat(config): read article classification and size settings from settings.toml`.
- [x] **TASK-03: Group `quality` (level thresholds and text sampling)**
  - **Scope**: `settings.toml` sections `[quality]`, `[quality_text_sample]`, `[quality_level]`; `src/infrastructure/env_config.py`; tests that asserted the old defaults 400 and 8000.
  - **Outcome**: 12 values read from `[quality]`, `[quality_text_sample]`, `[quality_level]` with the values of the local `.env` (`min_sample_word_count = 10000`, `character_limit = 32000`). Four asserts expecting 400/8000 (`test_env_config.py`, `test_analyze_document_use_case_wiring.py`) now expect 10000/32000. `QUALITY_THRESHOLD` is a recommendation threshold and stays for TASK-04. Verified by gentle-ai-verify: `src` 1600 OK, `tests` 51 OK, ruff clean. Native review (1 lens, medium risk) approved and acknowledged.
  - **Commit**: `695f47e` `feat(config): read quality sampling and level settings from settings.toml`.
- [x] **TASK-04: Group `recommendation` thresholds**
  - **Scope**: `settings.toml` section `[recommendation]` (10 thresholds, including `QUALITY_THRESHOLD`), `src/infrastructure/env_config.py`, tests asserting the values.
  - **User decision (2026-10-05)**: remove the two pre-existing `#` comments above `publish_threshold` in `env_config.py` (they break the no-inline-comments rule); the `[recommendation]` section name replaces them.
  - **Outcome**: 10 thresholds read from `[recommendation]` with the values of the local `.env`; the two `#` comments are gone. Verified by gentle-ai-verify: `src` 1603 OK, `tests` 51 OK, ruff clean. Parity check by the parent: `EnvConfig` built from `settings.toml` alone equals `EnvConfig` built from the local `.env` for all 40 migrated attributes (no differences). Native review (1 lens, medium risk) approved and acknowledged.
  - **Commit**: `73d8221` `feat(config): read recommendation thresholds from settings.toml`.
- [x] **TASK-05: Group `report` and `upload`**
  - **Scope**: `settings.toml` sections `[report]` (6 values) and `[upload]` (1 value), `src/infrastructure/env_config.py`, tests.
  - **Note**: `UPLOAD_MAX_SIZE_BYTES` is not in the local `.env`, so `settings.toml` carries the code default (26214400, 25 MiB).
  - **Outcome**: 7 values read from `[report]` and `[upload]`. Verified by gentle-ai-verify: `src` 1607 OK, `tests` 51 OK, ruff clean. Parity check by the parent: `EnvConfig` built from `settings.toml` alone equals the one built from the local `.env` for all 47 migrated attributes (no differences). What remains with `getenv` in `EnvConfig` is deployment or mode configuration and the Ollama/LLM tuning values, still open for the user. Native review (1 lens, medium risk) approved and acknowledged.
  - **Commit**: `9f39e5c` `feat(config): read report and upload settings from settings.toml`.
- [x] **TASK-06: Documentation and final verification** (full `src` and `tests` suites, ruff, pyright)
  - **Scope**: `README.md` (new "Configuration files" section), `openspec/specs/analyze-document/spec.md` (EnvConfig requirement, regenerated variable table with a `Source` column and `UPLOAD_MAX_SIZE_BYTES`, 4 new scenarios). `openspec/changes/archive/` is history and was not touched.
  - **Outcome**: final verification of the branch by gentle-ai-verify: `src` 1607 OK, `tests` 51 OK, ruff clean, no `#` comments, no local imports, no `raise ValueError` in the new production code. Pyright was not run: it is not installed in `.venv` (the agent did not install it). Native review not run on this docs-only candidate.
  - **Open for the user** (resolved 2026-10-06): the Ollama and external LLM values stay in `.env`; see the decision in section 2.
  - **Commit**: `42d444b` `docs(config): document settings.toml in the README and the analyze-document spec`.
- [-] **TASK-07: Group `ollama` and `external_llm` tuning (4 values)** (cancelled by the user on 2026-10-06; never committed)
  - **Outcome**: implemented, verified (`src` 1618 OK, `tests` 51 OK) and approved by the native review, then discarded before the commit because the user changed their mind: `OLLAMA_THINK`, `OLLAMA_MODEL_KEEP_ALIVE`, `OLLAMA_WARMUP_ON_STARTUP` and `EXTERNAL_LLM_THINK` stay in `.env`. The working tree went back to the state of commit `42d444b` (no `read_boolean`, no `[ollama]` or `[external_llm]` section).
- [x] **TASK-08: Remove the hardcoded defaults of the `.env` parameters in `EnvConfig`**
  - **User decision (2026-10-06)**: remove the default values from `src/infrastructure/env_config.py` to avoid silent failures. A missing parameter must stop the application with a message naming it.
  - **Scope**: `src/infrastructure/env_config.py`; test support (`src/infrastructure/tests/isolated_test_environment.py`, new `src/infrastructure/tests/test_doubles/complete_test_environment.py`); the tests that build `EnvConfig` or patch `os.environ`; `openspec/specs/analyze-document/spec.md` (Default column) and README if they state those defaults.
  - **Parameters that lose their default** (they live in `.env`; `SILVINA_APP_NAME` was in the first list but the user restored its default by hand before the commit, so 10 parameters lose it): `APP_MODE`, `LOG_LEVEL`, `LOG_RETENTION_DAYS`, `OLLAMA_MODEL_NAME`, `OLLAMA_BASE_URL`, `OLLAMA_THINK`, `OLLAMA_MODEL_KEEP_ALIVE`, `OLLAMA_WARMUP_ON_STARTUP`, `USE_EXTERNAL_LLM`, `EXTERNAL_LLM_THINK`. `METRICS_DATABASE_PATH` and `LOG_FILE_PATH` already had none.
  - **Deliberately unchanged**: `OLLAMA_NUM_CTX` (absence means "let Ollama decide", it has no default value), `LLM_PROVIDER` and `EXTERNAL_LLM_MODEL_NAME` (required only when the external LLM is active in `DEBUG`), and the testing-mode fallback `SILVINA_VERSION` = `"0.9"` (only active when `TESTING` is set; spec scenario).
  - **Design**: a missing or blank parameter raises `SettingValueMissing` (domain exception) naming the variable; `_get_required_env` switches from `ValueError` to it too, so there is one mechanism. Invalid formats keep their current errors. Tests get a deterministic complete environment (`CompleteTestEnvironment`) applied by `IsolatedTestEnvironment` and reused by the tests that use `clear=True`, so they no longer depend on the developer's `.env` or on removed defaults.
  - **Risk to check**: `load_dotenv()` only runs when the two wiring modules are imported; every real entry point (`main.py`, `web_main.py`, FastAPI) must still load `.env` before `EnvConfig()` is built.
  - **Outcome**: delegated to `gentle-ai-worker` (test-first, 39 RED failures/errors). The 11 parameters (10 after the manual change below) now go through `_get_required_env` and raise `SettingValueMissing` when missing or blank; `_parse_boolean` and the keep-alive parser lost their defaults; `CompleteTestEnvironment` and `IsolatedTestEnvironment.apply()` give the tests a complete deterministic environment; 5 existing test modules moved off `REQUIRED_ENVIRONMENT`. README and the `analyze-document` spec updated (`— (required)` rows, new `USE_EXTERNAL_LLM` and `EXTERNAL_LLM_THINK` rows, new missing-parameter scenario).
  - **Incident**: the worker reported `src` 1607 OK, but the independent verifier found 5 stale duplicated blocks (15 duplicate tests) in `test_env_config_settings_file.py` still using the removed `REQUIRED_ENVIRONMENT` (3 errors, 15 ruff F811). The parent confirmed it in the file, removed lines 195-359 and had the verification repeated. Lesson: never accept a worker report as evidence; the verifier is the check.
  - **Verification**: gentle-ai-verify second run: `src` 1607 OK, `tests` 51 OK, ruff clean, no `REQUIRED_ENVIRONMENT`, no `#` comments, the only value default left in `EnvConfig` is the `SILVINA_VERSION` testing fallback (the remaining `getenv(..., "")` are `TESTING`, `LLM_PROVIDER` and `EXTERNAL_LLM_MODEL_NAME`, empty-means-absent checks kept on purpose). Parent checks: `main`, `web_main`, the FastAPI app and its dependencies module all load `.env` before `EnvConfig()` (clean process, real `.env`); with `OLLAMA_BASE_URL` removed the error is `SettingValueMissing ... environment variable OLLAMA_BASE_URL is not set or is blank (define it in the .env file)`.
  - **Manual change by the user (2026-10-06)**: `SILVINA_APP_NAME` keeps `getenv("SILVINA_APP_NAME", "Silvina Editorial Assistant")`. The parent aligned the two missing/blank tests (list of 10), added `test_silvina_app_name_defaults_when_env_var_is_absent`, and set the spec row back to its default. The native review ran before this one-line change; it was not repeated because it only restores the previous behavior of one parameter.
  - **Commit**: pending the user's approval.
