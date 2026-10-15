# Feature: Settings Tests Independent of the Configuration Files

- **Feature Name**: `settings-tests-independent-of-config`
- **File Locator**: `odd/tasks/settings-tests-independent-of-config.md`
- **Branch**: `chore/raise-text-limits` (on top of `silvina_editorial_v100` at `acbe415`; the config commit `bd74c9d` is already there)
- **TDD Mode**: Test-only change. Value: each new test must fail when its mapping is mutated (mutation-checked); no production code changes
- **TDD Runner**: `export USE_EXTERNAL_LLM=false APP_MODE=PROD; .venv/Scripts/python.exe -m unittest discover -s src -t . -p "test_*.py"`
- **Commit policy**: separate commits in the order docs -> fix -> test (the fix commit is omitted: no production code changes); no push, PR or merge without the user's order

---

## 1. Problem

`EnvConfig` has no default values in code: every setting is read from `analysis_settings.toml` through `SettingsFileLoader` and `SettingsValueResolver`. About 17 tests build `EnvConfig()` with the real project file and assert the numbers it currently holds (for example `grammar_max_chars == 5000`). They verify the file, not the code, so any legitimate tuning of the file breaks the suite. Raising the text limits (commit `bd74c9d`) breaks 10 of them:

- `test_env_config.py`: `test_defaults_are_loaded_when_env_is_empty`, `test_get_classification_text_sampling_settings_returns_dto_with_defaults`, `test_get_language_tool_settings_returns_settings_with_defaults`, `test_get_quality_text_sampling_settings_returns_dto_with_defaults`.
- `test_env_config_settings_file.py`: `test_project_settings_file_provides_the_grammar_structure_and_citation_values`, `..._article_classification_and_size_values`, `..._quality_values`.
- `test_analyze_document_use_case_wiring.py`: `test_default_grammar_adapter_parameters_when_env_vars_absent`, `test_default_quality_text_sampler_parameters_when_env_vars_absent`, `test_default_article_classification_text_sampler_parameters_when_env_vars_absent`.

Others follow the same pattern and only pass because their values were not changed (recommendation, report/upload, eumic, `default_thresholds_when_env_vars_absent`, and similar).

## 2. Criterion (user, 2026-10-15)

A test is necessary when it checks code, not when it checks a configuration file. No test may depend on the values of a configuration file, not even the example. A DTO without behavior gets no test of its own.

## 3. Mapping result (text analysis, not measured coverage)

47 attributes of `EnvConfig` are read from the settings file through three generic functions. 29 have at least one test whose value is controlled by the test; 18 have none (only tests that assert the file's value, or no test). The only per-attribute defect such tests can detect is a crossed key (an attribute reading another attribute's key).

## 4. Design

- **A. Test-owned settings.** A test double with a complete TOML text where every key has a distinct, recognizable value. The loader requires every key (`SettingValueMissing`), so the text must be complete.
- **B. Mapping test.** Writes that TOML to a temporary directory, builds `EnvConfig(settings_file_path=...)` and asserts all 47 attributes against their unique values.
- **C. Builder tests.** `get_recommendation_settings`, `get_quality_text_sampling_settings`, `get_classification_text_sampling_settings` and `get_language_tool_settings` asserted field by field against the same controlled settings.
- **D. Remove the file-value tests** listed above and migrate the tests that start from the real file and replace one line (`_write_project_settings_with`) to the test-owned settings.
- **Kept**: loader error tests (missing file, invalid TOML, missing value), environment-variable override tests. Optional: a smoke test that the real project file loads, with no value assertions, only if `test_project_resources.py` / `test_settings_file_loader.py` do not already cover it.
- **Wiring tests**: reuse a test wiring that overrides `_get_env_config` with an `EnvConfig` built from the test-owned settings if that is enough; otherwise remove them, because the attribute-to-DTO mapping is covered by B and C. No production code is changed for the sake of a test.

## 5. Tasks

- [x] **TASK-01: Test-owned settings double and mapping test (A, B)**
- [x] **TASK-02: Builder tests for the four `get_*_settings` (C)**
- [x] **TASK-03: Remove file-value tests and migrate the line-replacing tests (D); wiring tests decision**
- [x] **TASK-05: Same criterion for `editorial_norms.toml`** (user, 2026-10-15): `test_loads_real_project_editorial_norms_file` asserts the real file's values; `DocxEumicAdapterBuilderForTest` loads the real file as its default norms, so every adapter test depends on its numbers. Replace with test-owned norms and a load-only test of the real file.
- [x] **TASK-06: Remove the tests of behavior-less norms DTOs** (user, 2026-10-15): `test_editorial_norms_dto.py` (14 tests) and `test_structure_norms_dto.py` (3 tests) only checked immutability, `as_dict` and equality, which `dataclass` and `BaseDTO` already provide (`test_base_dto.py` covers `BaseDTO`). The norm validation lives in `EditorialNormsLoader` and stays tested there. Extended the same day to every test file of a DTO that has only fields (see section 8).
- [x] **TASK-04: Verify: full suite green with the raised limits, mutation checks (crossed keys fail, changed file values do not), ruff, measured with mutations instead of coverage**

## 6. Verification evidence

- `EnvConfig` reads 48 settings (the mapping analysis said 47); the mapping test covers 48. The test double `complete_test_settings.py` gives each a distinct value.
- Full suite: 2174 tests OK (2173 plus the real-file load test) with the raised limits (10 fewer than before: file-value tests were removed or replaced).
- The suite stays green when `analysis_settings.toml` is set back to the previous numbers (5000 / 32000), so no test depends on the file's values.
- Mutation checks, each restored and confirmed with an empty diff of `env_config.py`:
  - swapping the keys `grammar.max_paragraphs` and `grammar.max_chars`: 5 tests fail;
  - pointing the `max_chars` field of `get_language_tool_settings()` at `grammar_max_paragraphs`: 4 tests fail.
- `ruff check` and `ruff format --check` clean on `src/infrastructure/tests`.
- Coverage is not installed in the virtual environment and was not installed; mutation checks replace it.

TASK-05 (`editorial_norms.toml`): `test_loads_real_project_editorial_norms_file` was replaced by `test_loads_real_project_editorial_norms_file_into_complete_dto`, which asserts only the DTO and section types, so it no longer depends on any value of the file. `DocxEumicAdapterBuilderForTest` and the `AnalyzeDocumentUseCaseWiringForTest` double now use the test-owned `build_editorial_norms_for_test()` (`src/domain/tests/dtos/editorial_norms_builder_for_test.py`), and the duplicate `_make_editorial_norms` helper in `test_docx_eumic_adapter.py` was removed in its favour. Two wiring tests that asserted the real file's values (`font_size_pt`, the `resumen` alias) now assert that the wiring hands the test-owned norms to the port and the structure validator. Full suite: 2174 tests OK with the real file unchanged and again with `margin_cm = 3.0` and `font_size_pt = 11` (both restored; `git diff -- editorial_norms.toml | wc -l` is 0). Removing `[keywords] min_count` makes the load-only test fail with `EditorialNormMissing` (restored, empty diff). `ruff check` and `ruff format --check` are clean on `src/infrastructure/tests` and `src/domain/tests`.

## 7. Known limits

- Tests that only override environment variables still build `EnvConfig()` with the default settings path, so they load the real file without asserting its values. Avoiding that needs a change to the production default and was left out.
- `editorial_norms.toml` was still asserted by a test (`font_size_pt == 12.0`); moved into this branch as TASK-05.
- `test_project_resources.py` and `test_settings_file_loader.py` do not assert values. A single test, `test_project_settings_file_provides_every_setting_with_the_expected_type`, loads the real `analysis_settings.toml` and checks only that every setting exists with the right type. Removing a key from the real file makes it fail with `SettingValueMissing`; changing values leaves it green.
- The removed default tests also asserted some environment values (`ollama_base_url`, `log_retention_days`); those assertions are only partly covered by other tests.

## 8. TASK-06 evidence

- The seven norms DTOs (`DocumentFormatNormsDTO`, `CaptionNormsDTO`, `AbstractNormsDTO`, `KeywordNormsDTO`, `StructureNormsDTO`, `EditorialNormsDTO`) have no `__post_init__`, validation or methods, only fields.
- Both test files deleted: 17 tests removed. Full suite: 2157 tests OK (2174 minus 17); `ruff check` and `ruff format --check` clean.
- Extension (user, 2026-10-15): reviewed `src/domain/tests/dtos` against the DTO sources. 34 of 45 DTO classes have only fields. 19 more test files checked only fields, defaults, frozen behavior, `as_dict`/`from_dict` or equality, and were deleted (76 tests): `ai_interaction`, `analysis_completion`, `analysis_start`, `apa_validation_result`, `apa_violation`, `classification_signals`, `classification_text_sampling_settings`, `classified_feedback_line`, `dimension_score`, `eumic_violation`, `feedback_block`, `feedback_line`, `grammar_check_result`, `grammar_error`, `llm_generation`, `parsed_response`, `quality_text_sampling_settings`, `stage_duration` and `citation_extraction_result`. No other file imported them.
- Full suite after the extension: 2081 tests OK (2157 minus 76); `ruff check` and `ruff format --check` clean.
- Kept because they check code: `test_base_dto`, `test_document_content_dto_display_authors`, and the tests of `__str__`, `to_dict`, `create`, `effective_structure_type` and `__post_init__` inside `test_analysis_result`, `test_citation`, `test_citation_analysis_result`, `test_classification_result`, `test_document_content`, `test_quality_result`, `test_reference`, `test_section` and `test_structure_validation_result`. Those nine files also contain generic tests (subclass of `BaseDTO`, immutability, field values) that were not removed.
