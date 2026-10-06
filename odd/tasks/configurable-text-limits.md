# Feature: Configurable Text Sampling and Grammar Limits

- **Feature Name**: `configurable-text-limits`
- **File Locator**: `odd/tasks/configurable-text-limits.md`
- **Branch**: `feat/configurable-text-limits` (from `silvina_editorial_v100` at `abd5c84`)
- **TDD Mode**: Test-first for every behavior change (RED then GREEN)
- **TDD Runner**: `export USE_EXTERNAL_LLM=false APP_MODE=PROD; .venv/Scripts/python.exe -m unittest discover -s src -t . -p "test_*.py"` and the same with `-s tests` (do NOT invoke a test module directly, it gives false `METRICS_DATABASE_PATH` errors)
- **Commit policy**: no commit until the user ordered it on 2026-10-05; committed afterwards as `2c6a4e5` (code, tests, specs) plus a `docs(odd)` commit for this document; push only on the user's order
- **Edit-tool restriction**: the Gentle AI safety policy may block writing `.env.example`; if so the user edits it by hand from the lines listed in TASK-04

---

## 1. Objective

Remove the hardcoded limits that decide how much of an article is analyzed, and expose them as `.env` parameters read by `EnvConfig` and injected through the wiring. This is the first step of the larger change analysed on 2026-10-05 (analysing the full article instead of samples); the model context size (`num_ctx`) is NOT part of this step.

## 2. Findings that define the scope

- `QualityTextSampler` already takes constructor parameters, but `EnvConfig` and the wiring only pass `QUALITY_MIN_SAMPLE_WORD_COUNT` and `QUALITY_TEXT_SAMPLE_CHARACTER_LIMIT`. The other six `QUALITY_TEXT_SAMPLE_*` variables present in `.env` and `.env.example` are read by nobody (inert): `REFERENCE_LINE_PREFIX_LENGTH`, `INTRODUCTION_PARAGRAPH_COUNT`, `MIDDLE_PARAGRAPH_COUNT`, `CONCLUSION_PARAGRAPH_LIMIT`, `FALLBACK_TAIL_PARAGRAPH_COUNT`, `CONCLUSION_HEADER_MARKER` (the last one is a hardcoded regex `conclusi` in the class).
- `ArticleClassificationTextSampler` hardcodes 3500 / 2500 / 6000 characters and a bibliography header length of 30; the wiring instantiates it without parameters.
- `LanguageToolAdapter` hardcodes `_MAX_PARAGRAPHS = 20`, `_MAX_CHARS = 5000`, `_MAX_ERRORS = 10` as module constants.

## 3. Design

- Samplers and the adapter receive every limit as a required constructor parameter (no defaults in the class); the default values live only in `EnvConfig` (`getenv(name, default)`), preserving today's behavior when the variables are absent.
- `EnvConfig` reads and casts each new variable (fail-fast `int()`), the wiring injects them. Domain classes never import infrastructure.
- Behavior with the default values must be byte-identical to today.
- New variables (default in parentheses):
  - `QUALITY_TEXT_SAMPLE_*`: wire the six existing variables (80, 3, 2, 3, 2, `conclusi`).
  - `ARTICLE_CLASSIFICATION_SAMPLE_INTRODUCTION_CHARACTER_LIMIT` (3500), `ARTICLE_CLASSIFICATION_SAMPLE_CONCLUSION_CHARACTER_LIMIT` (2500), `ARTICLE_CLASSIFICATION_SAMPLE_FALLBACK_CHARACTER_LIMIT` (6000), `ARTICLE_CLASSIFICATION_BIBLIOGRAPHY_HEADER_MAX_LENGTH` (30).
  - `GRAMMAR_MAX_PARAGRAPHS` (20), `GRAMMAR_MAX_CHARS` (5000), `GRAMMAR_MAX_ERRORS` (10).

## 4. Out of scope (hardcoded values left untouched on purpose)

- Output-field truncation in the wiring (`_SUITABILITY_*_MAX_LENGTH`), EUMIC document-format standards (`eumic_document_standards.py`, `eumic_violation_factory.py`), grammar score levels, the bibliography marker vocabulary, the LanguageTool language (`es`). They do not decide how much of the article is analyzed.
- `num_ctx` for Ollama and any change to sampling strategy: later steps, on the user's instruction.

## 5. Tasks

- [x] **TASK-01: Quality sampler**
  - **Scope**: `src/domain/quality/quality_text_sampler.py`, `src/infrastructure/env_config.py`, `src/infrastructure/wirings/analyze_document_use_case_wiring.py`, tests under `src/domain/tests/quality/` and `src/infrastructure/tests/`.
  - **Outcome**: the six inert variables take effect; `conclusion_header_marker` becomes a constructor parameter.
- [x] **TASK-02: Classification sampler**
  - **Scope**: `src/domain/classification/article_classification_text_sampler.py`, `env_config.py`, wiring, tests under `src/domain/tests/classification/` and `src/infrastructure/tests/`.
- [x] **TASK-03: Grammar adapter**
  - **Scope**: `src/infrastructure/adapters/grammar/language_tool_adapter.py`, `env_config.py`, wiring, `src/infrastructure/tests/test_language_tool_adapter.py`.
- [x] **TASK-04: Configuration files and docs** (openspec specs updated by the worker; `.env` and `.env.example` edited by the user by hand, 7 variables confirmed present in both on 2026-10-05)
  - **Scope**: `.env` (local, gitignored), `.env.example`, `openspec/specs/analyze-document/spec.md` variable table if it lists these variables.
  - **Lines for .env / .env.example** (to be added manually due to agent safety policy):
    ```env
    # Article classification sample limits
    ARTICLE_CLASSIFICATION_SAMPLE_INTRODUCTION_CHARACTER_LIMIT=3500
    ARTICLE_CLASSIFICATION_SAMPLE_CONCLUSION_CHARACTER_LIMIT=2500
    ARTICLE_CLASSIFICATION_SAMPLE_FALLBACK_CHARACTER_LIMIT=6000
    ARTICLE_CLASSIFICATION_BIBLIOGRAPHY_HEADER_MAX_LENGTH=30

    # Grammar analysis limits
    GRAMMAR_MAX_PARAGRAPHS=20
    GRAMMAR_MAX_CHARS=5000
    GRAMMAR_MAX_ERRORS=10
    ```
- [x] **TASK-05: Verification**
  - **Scope**: full `src` and `tests` unittest suites, ruff, behavior parity with default values.
  - **Evidence (gentle-ai-verify, 2026-10-05)**: `src` suite 1498 tests OK; `tests` suite 49 tests OK; ruff check and format clean on 13 files; structural greps clean; `conclusion_header_marker` parity with the old `conclusi` regex confirmed on 3 headings.
  - **Notes**: `QualityTextSampler` and the other two classes no longer have constructor defaults (external callers would break); `LanguageToolAdapter.check` gained an unreachable `if self._tool is None` type-narrowing guard not in the design (candidate to revert).
  - **Commit**: none, by the user's order.

- [x] **TASK-06: Group the limits into settings objects (user decision 2026-10-05)**
  - **Decision**: pass each class its limits as one immutable settings object instead of individual parameters, following the existing precedent (`ArticleSizeThresholdsDTO`, `RecommendationSettingsDTO` built by `EnvConfig.get_recommendation_settings()`, `DocxReportSettings`).
  - **Design**: `QualityTextSamplingSettingsDTO` (8 fields: `min_sample_word_count`, `text_sample_character_limit`, `reference_line_prefix_length`, `introduction_paragraph_count`, `middle_paragraph_count`, `conclusion_paragraph_limit`, `fallback_tail_paragraph_count`, `conclusion_header_marker`) and `ClassificationTextSamplingSettingsDTO` (4 fields: `introduction_character_limit`, `conclusion_character_limit`, `fallback_character_limit`, `bibliography_header_max_length`) in `src/domain/dtos/`, `@dataclass(frozen=True)` over `BaseDTO`, no defaults; `LanguageToolSettings` (`max_replacements`, `max_paragraphs`, `max_chars`, `max_errors`) as a frozen dataclass in `src/infrastructure/adapters/grammar/language_tool_settings.py`. `EnvConfig` exposes `get_quality_text_sampling_settings()`, `get_classification_text_sampling_settings()`, and `get_language_tool_settings()`; the wiring injects them. `language` keeps its default on the adapter.
  - **Outcome**: `QualityTextSampler`, `ArticleClassificationTextSampler`, and `LanguageToolAdapter` constructors refactored to accept single immutable settings objects. Wiring injects settings objects cleanly. The type-narrowing guard `if self._tool is None: raise GrammarCheckUnavailable()` in `LanguageToolAdapter.check` was retained because pyright flags `self._tool.check(text)` when removed.
  - **Evidence**: unit tests for all three settings objects (immutability via `FrozenInstanceError`, required fields, `as_dict`/`from_dict` round trip for DTOs), `EnvConfig` getter tests with defaults and overrides, sampler unit tests, and wiring tests verifying default and overridden parameter propagation to instances.

- [x] **TASK-07: Descriptive rename of settings constructor parameters and attributes**
  - **Scope**: `src/domain/quality/quality_text_sampler.py`, `src/domain/classification/article_classification_text_sampler.py`, `src/infrastructure/adapters/grammar/language_tool_adapter.py`, `src/infrastructure/wirings/analyze_document_use_case_wiring.py`, associated unit tests, and openspec documentation.
  - **Rename Mapping**:
    - `QualityTextSampler`: constructor parameter `settings` -> `quality_text_sampling_settings`, instance attribute `self._settings` -> `self._quality_text_sampling_settings`.
    - `ArticleClassificationTextSampler`: constructor parameter `settings` -> `classification_text_sampling_settings`, instance attribute `self._settings` -> `self._classification_text_sampling_settings`.
    - `LanguageToolAdapter`: constructor parameter `settings` -> `language_tool_settings`, instance attribute `self._settings` -> `self._language_tool_settings`.
  - **Outcome**: constructor parameters, instance attributes, instantiation call sites, tests, and spec references updated to descriptive names. Unrelated settings references (e.g. `RecommendationBuilder`, `DocxReportAdapter`) left untouched.

- [x] **TASK-08: Descriptive rename of RecommendationBuilder and DocxReportAdapter settings**
  - **Scope**: `src/domain/recommendation/recommendation_builder.py`, `src/infrastructure/adapters/report/docx_report_adapter.py`, `src/infrastructure/wirings/analyze_document_use_case_wiring.py`, `src/infrastructure/wirings/export_report_wiring.py`, associated unit tests under `src/infrastructure/tests/`, and openspec documentation.
  - **Rename Mapping**:
    - `RecommendationBuilder`: constructor parameter `settings` -> `recommendation_settings`, instance attribute `self._settings` -> `self._recommendation_settings`.
    - `DocxReportAdapter`: constructor parameter `settings` -> `docx_report_settings`, instance attribute `self._settings` -> `self._docx_report_settings`.
  - **Outcome**: constructor parameters, instance attributes, instantiation call sites, tests, and spec references updated to descriptive names. Note: `AnalysisContext.settings` (and `context.settings` usages) was intentionally left untouched as out of scope.
