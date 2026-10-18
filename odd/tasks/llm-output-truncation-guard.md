# Feature: Per-Call Output Limits and Truncation Guard

- **Feature Name**: `llm-output-truncation-guard`
- **File Locator**: `odd/tasks/llm-output-truncation-guard.md`
- **Branch**: `fix/llm-output-truncation-guard` (from `silvina_editorial_v200`)
- **TDD Mode**: Enabled (RED -> GREEN -> REFACTOR) where a runnable test applies
- **TDD Runner**: `.venv/Scripts/python -m pytest -q src tests`
- **Delivery Strategy**: one work-unit commit per task on the feature branch; push, pull request and merge are requested explicitly by the user

---

## 1. Objective

An output cut by the output-token limit must fail with a clear error instead of being parsed as if it were complete, and the single `num_predict = 300` limit shared by unrelated calls is replaced by one limit per call.

## 2. Why

- `num_predict = 300` comes from the legacy classifier (it had 200, then 10 for a one-word answer, then 300 for the S4/S5/S6 lines). The hexagonal migration copied it into `[article_classifier]` and the editorial suitability analyzer reused it under that misleading name. The quality calls send no limit at all, and `ClaudeGeneratorAdapter` ignores the options.
- Measured on `metrics.db` with Ollama and the original prompts, all 289 recorded calls ended with `done_reason = stop`. Output tokens: classification 15, suitability 64 to 202, quality 379 to 728. The 300 never binds today, and its margin over suitability is only 1.5 times.
- A cut response is silent: a missing verdict falls back to the first enum member (`NO SUSTENTADA`, `NO ALINEADO`), a missing S4/S5/S6 line is read as `False`, and a missing score becomes the default 7.0. `AuditedLlmGeneratorAdapter` only logs a warning when `done_reason` is `length`.

## 3. Agreed specification

- When the backend reports `done_reason = length`, the call raises a clear error (new `LanguageModelOutputTruncated` in `language_model_errors.py`) and the analysis fails. Recording the interaction and the existing warning stay as they are.
- One output limit per call, each with its own settings key and environment variable, in a new `[llm_output_limits]` section of `analysis_settings.toml`:
  - `article_classification_max_output_tokens = 128` (`ARTICLE_CLASSIFICATION_MAX_OUTPUT_TOKENS`)
  - `editorial_suitability_max_output_tokens = 1000` (`EDITORIAL_SUITABILITY_MAX_OUTPUT_TOKENS`)
  - `quality_analysis_max_output_tokens = 4096` (`QUALITY_ANALYSIS_MAX_OUTPUT_TOKENS`)
- `[article_classifier] num_predict` and `ARTICLE_CLASSIFIER_NUM_PREDICT` are removed. `[article_classifier] temperature` stays (shared by the classifier and the suitability analyzer; renaming it is out of scope).
- The quality analyzer starts sending `{"num_predict": limit}` and nothing else, so its temperature stays as it is.
- The domain options key stays `num_predict` because it is the Ollama option name; the Claude adapter keeps ignoring options.
- The guard is a decorator adapter around the audited generator, composed in the wiring.

## 4. Constraints

- Follow `.agent/skills/clean-architecture/SKILL.md`.
- The settings file is read fail-fast; the environment variable of the same name overrides it.
- `.env` and `.env.example` are edited by the user only.
- Behavior with a response that ends with `stop` must not change.

## 5. Tasks

- [x] **TASK-01** Per-call output limits: new settings and `EnvConfig` attributes, `ArticleClassifier` and `EditorialSuitabilityAnalyzer` take `max_output_tokens` instead of `num_predict`, `QualityAnalyzer` sends its limit, wiring updated, old setting removed. RED first.

- [x] **TASK-02** Truncation guard: `LanguageModelOutputTruncated`, a decorator adapter that raises it when `done_reason` is `length`, composed in `_get_llm_generator` around the audited adapter. RED first.

## 6. Open items

- Native review of the whole slice (3 commits, 27 files, 642 lines, base `2784a59`) was approved and acknowledged (lineage `review-0209109b795bdf08`, medium risk, lens `review-reliability`, authority burned). Advisory findings, non-blocking, location only (the provider returns no text): R3-001 WARNING `analysis_settings.toml:18`, R3-002 WARNING `env_config.py:45-59`, R3-003 WARNING `analysis_settings.toml:17-20`, R3-004 WARNING `test_env_config_settings_file.py:199-236`, R3-005 WARNING `analyze_document_use_case_wiring.py:463-473`, R3-006 SUGGESTION `test_analyze_document_use_case_wiring.py:365`. Separate later work. One point reasoned by the parent, not confirmed by the findings and not verified in the code: the three limits are read as integers without checking that they are positive.
- The default review candidate of this repository is a base diff of about 1100 paths; the slice was reviewed with an explicit full-sha `baseRef` and `committedOnly`.

## 7. Evidence

### TASK-01
- RED: 76 failed, 2252 passed before touching production code (cascade: the settings double lost `num_predict` while `EnvConfig` still required it, and the constructors did not accept `max_output_tokens`).
- GREEN: baseline 2318 passed, final 2325 passed (191 subtests), re-run by the parent; `ruff check` and `ruff format --check` clean. 19 files, all inside the allowed surfaces; no reference to the old `article_classifier_num_predict` is left.
- New tests (logic only): the three limits read from the settings file and overridden by environment variable, fail-fast naming the key, wiring of the limits into the classifier and the quality analyzer, and the quality analyzer sending only `{"num_predict": limit}` in both calls.
- If a local `.env` still defines `ARTICLE_CLASSIFIER_NUM_PREDICT`, it is no longer read. The three new limits work with the settings file defaults.
- Not touched: `docs/full-text-refactor/02-text-limits-inventory.md` (study document, line 34 still mentions the old key).

### TASK-02
- RED: the new and the changed test modules did not import before the implementation (the symbols did not exist), so the new tests were blocked and not run one by one; the wiring modules that could not be collected account for the 62 missing tests of that pass (2263 passed against the 2325 baseline). Blocked new tests include `test_generate_with_usage_raises_output_truncated_when_done_reason_is_length`, `test_generate_raises_output_truncated_when_done_reason_is_length` and `test_truncated_generation_is_recorded_before_the_guard_raises`.
- GREEN: baseline 2325 passed, final 2336 passed (191 subtests), re-run by the parent; `ruff check` and `ruff format --check` clean. All changed files are inside the allowed surfaces.
- `TruncationGuardLlmGeneratorAdapter` wraps the audited generator in `_get_llm_generator`, so the audit still records the interaction with `done_reason = length` before the guard raises `LanguageModelOutputTruncated`. The warm-up goes through its own adapter and is not affected.
- Claude: `CLAUDE_STOP_REASON_TO_DONE_REASON` already maps `max_tokens` and `model_context_window_exceeded` to `length`, so the guard also covers a response cut by the Claude backend. Claude still ignores the generation options.
