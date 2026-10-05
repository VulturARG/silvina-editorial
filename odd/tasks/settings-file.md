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
- Value policy: `settings.toml` starts from the values the user runs today in the local `.env` (the user authorized reading it). Where `.env` differs from the code default, ask which value `settings.toml` should carry.
- Gotcha: a line left in the local `.env` overrides `settings.toml`. The user decided `.env` keeps its parameters; the agent never edits `.env`.
- Stays in `.env` for now (deployment or mode, not tuning): `APP_MODE`, `METRICS_DATABASE_PATH`, `LOG_FILE_PATH`, `LOG_LEVEL`, `LOG_RETENTION_DAYS`, `OLLAMA_BASE_URL`, `USE_EXTERNAL_LLM`, `LLM_PROVIDER`, `EXTERNAL_LLM_MODEL_NAME`, `SILVINA_APP_NAME`.
- Open: the Ollama tuning values (`OLLAMA_MODEL_NAME`, `OLLAMA_THINK`, `OLLAMA_MODEL_KEEP_ALIVE`, `OLLAMA_NUM_CTX`, `OLLAMA_WARMUP_ON_STARTUP`, `EXTERNAL_LLM_THINK`) are decided with the user after the main groups.

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
  - **Outcome**: 12 values (2 classifier, 4 classification sampling, 6 size bands) read from `[article_classifier]`, `[article_classification]`, `[article_size]`. User decision: `sample_introduction_character_limit = 32000` (the value in use in `.env`), not the old default 3500; the two assertions in `test_env_config.py` and the one in `test_analyze_document_use_case_wiring.py` that expected 3500 now expect 32000 (the wiring one was found by the first verifier run). Verified by gentle-ai-verify: `src` 1597 OK, `tests` 51 OK, ruff clean.
  - **Commit**: pending the user's approval.
- [ ] **TASK-03: Group `quality` (level thresholds and text sampling)**
- [ ] **TASK-04: Group `recommendation` thresholds** (also decide on the two pre-existing `#` comments above `publish_threshold` in `env_config.py`, which break the no-inline-comments rule)
- [ ] **TASK-05: Group `report` and `upload`**
- [ ] **TASK-06: Documentation and final verification** (full `src` and `tests` suites, ruff, pyright)
