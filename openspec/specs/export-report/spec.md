# Report Export — Hexagonal Layer Specification
## Slice 12 (export-report)

## Purpose

Defines the port, DTO, exception, adapter, use case, wiring, and fake double that expose `.docx` report export as a testable hexagonal service, while leaving `presentation/word_exporter.py` untouched.

---

## Requirements

### Requirement: ReportExportPort Abstract Interface

`ReportExportPort(ABC)` MUST reside in `src/domain/report/` and declare one abstract method: `export(report_input: ReportInputDTO, path: str) -> bool`. The domain MUST NOT import from infrastructure or application layers.

#### Scenario: Concrete implementation satisfies the contract

- GIVEN a class implementing `export(report_input, path)`
- WHEN it is instantiated and passed as a `ReportExportPort`
- THEN no `TypeError` is raised

#### Scenario: Abstract class cannot be instantiated directly

- GIVEN `ReportExportPort` is abstract
- WHEN client code calls `ReportExportPort()`
- THEN Python raises `TypeError`

---

### Requirement: ReportInputDTO Is Frozen

`ReportInputDTO` MUST be a frozen dataclass in `src/domain/dtos/report_input_dto.py` with fields:
- `filename: str`
- `document_content: DocumentContentDTO`
- `classification: ClassificationResultDTO`
- `quality: QualityResultDTO`
- `grammar: GrammarCheckResultDTO`
- `structure: StructureValidationResultDTO`
- `citations: CitationAnalysisResultDTO`
- `apa_validation: ApaValidationResultDTO`
- `recommendations: list[RecommendationDTO]`
- `verdict: PublicationVerdictDTO`
- `eumic_violations: list[EumicViolationDTO]`

> Updated in Slice 13: `recommendations` is now `list[RecommendationDTO]` (was `list[dict]`). `verdict: PublicationVerdictDTO` and `eumic_violations: list[EumicViolationDTO]` were added.

#### Scenario: DTO is immutable after construction

- GIVEN a constructed `ReportInputDTO`
- WHEN any field is reassigned
- THEN Python raises `FrozenInstanceError`

#### Scenario: DTO holds typed verdict and recommendation lists

- GIVEN a valid instance of `ReportInputDTO`
- WHEN `recommendations`, `verdict`, and `eumic_violations` are read
- THEN `recommendations` is `list[RecommendationDTO]`, `verdict` is `PublicationVerdictDTO`, and `eumic_violations` is `list[EumicViolationDTO]`

---

### Requirement: ReportExportUnavailable Exception

`ReportExportUnavailable(SrcBaseWarning)` MUST be defined in `src/domain/exceptions/report_errors.py` with `MESSAGE = "The report export service is unavailable (python-docx not installed)."`.

#### Scenario: Exception carries the expected message

- GIVEN `ReportExportUnavailable` is raised and caught
- WHEN its `MESSAGE` attribute is read
- THEN it equals the defined string literal

---

### Requirement: DocxReportSettings Configuration Object

`DocxReportSettings` MUST be a frozen dataclass at `src/infrastructure/adapters/report/docx_report_settings.py`. Its 8 deployment-config fields are **required** (no defaults) — the wiring layer MUST supply them from `EnvConfig`:
- `app_name: str`
- `app_version: str`
- `score_high_threshold: float`
- `score_medium_threshold: float`
- `words_per_page: int`
- `max_errors_displayed: int`
- `context_truncation_limit: int`
- `max_replacements: int`

Its remaining fields (Word template visual constants: fonts, colors, sizes, table style, layout dimensions) keep static defaults and are NOT sourced from `EnvConfig` — they are design constants, not deployment config.

`DocxReportSettings` MUST NOT read environment variables directly.

(Previously: All 8 deployment fields had static defaults (`words_per_page: int = 250`, etc.), allowing `DocxReportSettings()` to be instantiated with zero arguments. Defaults were removed to fail fast if the wiring layer omits a deployment value, mirroring the `RecommendationSettingsDTO` no-defaults pattern.)

#### Scenario: Instantiation without deployment fields raises TypeError

- GIVEN no arguments are passed
- WHEN `DocxReportSettings()` is instantiated
- THEN Python raises a `TypeError` due to missing required arguments

#### Scenario: Visual template fields use static defaults when only deployment fields are provided

- GIVEN all 8 deployment fields are provided and no visual fields are provided
- WHEN `DocxReportSettings(...)` is instantiated
- THEN `settings.font_name`, `settings.table_style`, `settings.heading_color_rgb`, and other visual fields match their static defaults

#### Scenario: Settings accepts arguments passed during instantiation

- GIVEN all 8 deployment fields are provided, with `words_per_page=300` and `max_errors_displayed=10` overriding the rest
- WHEN `DocxReportSettings(...)` is instantiated
- THEN `settings.words_per_page == 300` AND `settings.max_errors_displayed == 10`

---

### Requirement: DocxReportAdapter Hard-Fails Without python-docx

`DocxReportAdapter.__init__` MUST raise `ReportExportUnavailable` at construction time when `DOCX_AVAILABLE` is `False`. The constructor MUST accept `settings: DocxReportSettings` as a **required** parameter (no default, no fallback construction) and an optional `logo_path`. The system SHALL NOT proceed to serve requests without python-docx installed.

(Previously: `settings` defaulted to `None` and fell back to a default-constructed `DocxReportSettings()`. This fallback is no longer possible because `DocxReportSettings` has no defaults for its 8 deployment-config fields.)

#### Scenario: Adapter raises at construction when python-docx is absent

- GIVEN `DOCX_AVAILABLE = False` and a valid `settings` object
- WHEN `DocxReportAdapter(logo_path=None, settings=settings)` is called
- THEN `ReportExportUnavailable` is raised before `__init__` returns

#### Scenario: Adapter initializes normally when python-docx is present

- GIVEN `DOCX_AVAILABLE = True` and a valid `settings` object
- WHEN `DocxReportAdapter(logo_path=None, settings=settings)` is called
- THEN no exception is raised

#### Scenario: Adapter construction fails without settings

- GIVEN no `settings` argument is provided
- WHEN `DocxReportAdapter(logo_path=None)` is called
- THEN Python raises a `TypeError` due to the missing required argument

---

### Requirement: DocxReportAdapter Produces Functionally Equivalent DOCX

`DocxReportAdapter.export()` MUST produce a `.docx` containing the same 11 sections as `WordExporter`, in order: title page, executive summary, document info, classification, quality analysis, grammar, APA validation, structure validation, citations, recommendations, footer. All 13 private rendering methods MUST remain private. Error wrapping is handled by `@generic_error_handler` at the use case layer, not the adapter.

The `DocxReportAdapter` MUST utilize configuration settings from `DocxReportSettings` instead of hardcoded magic values:
- Use `settings.words_per_page` for estimating pages (`estimated_pages = word_count // words_per_page`).
- Use `settings.max_errors_displayed` to limit the number of displayed grammar errors and APA validation violations.
- Use `settings.context_truncation_limit` to truncate grammar error context.
- Use `settings.max_replacements` to limit the number of replacements shown per grammar error.

The `_add_recommendations` method MUST render the publication verdict from `report_input.verdict` (a `PublicationVerdictDTO`) before the specific recommendations list. Color mapping: `PublicationVerdict.CRITICAL` and `PublicationVerdict.WARNING` → `reject_color_rgb`; `PublicationVerdict.APPROVED` → `publishable_color_rgb`. Specific recommendations use `RecommendationPriority` icons (`HIGH` → 🔴, `MEDIUM` → 🟡, `LOW` → 🟢) and attribute access (`rec.priority`, `rec.message`).

> Updated in Slice 13: `_add_recommendations` was refactored from dict-key access to attribute access. Verdict rendering was separated from the recommendations list (uses `report_input.verdict` directly, not a special entry in `recommendations`).

#### Scenario: Successful export returns True

- GIVEN a valid `ReportInputDTO` and a writable `path`
- WHEN `DocxReportAdapter.export(report_input, path)` is called
- THEN it returns `True` and a `.docx` file exists at `path`

#### Scenario: All 11 sections are present in the output

- GIVEN a valid `ReportInputDTO`
- WHEN `export()` completes
- THEN the output `.docx` contains: title page, executive summary, document info, classification, quality analysis, grammar, APA validation, structure validation, citations, recommendations, footer

#### Scenario: IO error propagates to caller

- GIVEN a path that cannot be written
- WHEN `DocxReportAdapter.export(report_input, path)` is called
- THEN the underlying `OSError` propagates; `@generic_error_handler` on the use case wraps it as `SrcGenericError`

#### Scenario: Settings are respected during rendering

- GIVEN a `DocxReportSettings` with `words_per_page` = 100, `max_errors_displayed` = 2, `context_truncation_limit` = 10, `max_replacements` = 1
- WHEN `DocxReportAdapter.export()` is called with this configuration
- THEN the exported report uses page estimation based on 100 words per page
- AND at most 2 grammar/APA errors are listed
- AND error contexts are truncated to 10 characters
- AND at most 1 replacement is shown per error

---

### Requirement: ExportReportUseCase Delegates to Port

`ExportReportUseCase` MUST accept `ReportExportPort` via constructor injection. `execute(report_input, path) -> bool` MUST be decorated with `@generic_error_handler` and MUST delegate directly to the injected port.

#### Scenario: Use case returns port result

- GIVEN `FakeReportExportPort` configured to return `True`
- WHEN `ExportReportUseCase.execute(report_input, path)` is called
- THEN it returns `True`

#### Scenario: Use case propagates port exceptions

- GIVEN `FakeReportExportPort` configured to raise `ReportExportUnavailable`
- WHEN `execute(report_input, path)` is called
- THEN `ReportExportUnavailable` propagates to the caller

---

### Requirement: FakeReportExportPort Enables Test Isolation

`FakeReportExportPort(ReportExportPort)` MUST reside in `src/domain/tests/report/` and support a configurable return value and an optional exception raise. It MUST satisfy the full port contract.

#### Scenario: Fake returns configured boolean

- GIVEN `FakeReportExportPort(return_value=False)`
- WHEN `export(report_input, path)` is called
- THEN it returns `False`

#### Scenario: Fake raises configured exception

- GIVEN `FakeReportExportPort(raise_error=ReportExportUnavailable)`
- WHEN `export(report_input, path)` is called
- THEN `ReportExportUnavailable` is raised

---

### Requirement: ExportReportWiring Assembles the Full Object Graph

`ExportReportWiring.create_use_case()` MUST resolve `logo_path` relative to the project root, instantiate `EnvConfig`, construct `DocxReportSettings` using values from the `EnvConfig` instance, instantiate `DocxReportAdapter` with that settings object, and return a fully wired `ExportReportUseCase`. It MUST raise `ReportExportUnavailable` at startup if python-docx is absent.

(Previously: Instantiated `DocxReportSettings` which read environment variables dynamically from `os.environ` via default factories.)

#### Scenario: Wiring returns a fully wired use case

- GIVEN python-docx is installed and `REPORT_WORDS_PER_PAGE=300` is set in the environment
- WHEN `ExportReportWiring.create_use_case()` is called
- THEN it returns an `ExportReportUseCase` whose port is a `DocxReportAdapter`
- AND the adapter's settings has `words_per_page == 300`

#### Scenario: Wiring fails at startup without python-docx

- GIVEN python-docx is not installed
- WHEN `ExportReportWiring.create_use_case()` is called
- THEN `ReportExportUnavailable` is raised

---

### Requirement: JsonReportAdapter Implements ReportExportPort

`JsonReportAdapter(ReportExportPort)` MUST reside in `src/infrastructure/adapters/report/json_report_adapter.py`, require no settings or configuration object, and serialize the given `ReportInputDTO` by (1) reproducing `main.py`'s `_map_report_to_legacy_dict` field mapping internally (duplicated logic, not imported from `main.py`) to obtain the legacy dict shape, then (2) applying a recursive Enum→`.value` / `BaseDTO`→`.as_dict()` conversion pass equivalent to `main.py`'s current `_prepare_for_json`, before writing with `json.dump(indent=2, ensure_ascii=False)`. A plain `ReportInputDTO.as_dict()` dump is explicitly insufficient: `ReportInputDTO`'s tree contains real `datetime` fields that crash naive serialization, and its structure differs from the legacy dict (renamed keys, computed fields, dropped/sliced fields) that is actually on disk today. Output structure MUST match today's real `main.py` `_map_report_to_legacy_dict()` + `_prepare_for_json()` + `json.dump()` pipeline exactly — this is a compatibility contract because the file is read by systems external to this application, not just an internal preference.

#### Scenario: Successful export returns True

- GIVEN a valid `ReportInputDTO` and a writable `path`
- WHEN `JsonReportAdapter.export(report_input, path)` is called
- THEN it returns `True` and a `.json` file exists at `path`

#### Scenario: Output is byte-for-byte identical to today's real production pipeline

- GIVEN a real sample `ReportInputDTO` fixture
- WHEN `JsonReportAdapter.export(report_input, path)` writes `path`, and separately today's real pre-change pipeline — `_map_report_to_legacy_dict(report_input)` then `_prepare_for_json(...)` then `json.dump(..., indent=2, ensure_ascii=False)` — writes `golden_path` from the same fixture
- THEN the raw bytes of `path` and `golden_path` are identical

#### Scenario: Nested Enum fields are converted to their .value

- GIVEN a `ReportInputDTO` fixture whose `recommendations[].priority` and `apa_validation.violations[].error_type` are Enum members (`verdict` is dropped by `_to_legacy_shape`'s field mapping, matching today's real output — not applicable here)
- WHEN `JsonReportAdapter.export(report_input, path)` is called
- THEN the written JSON contains the Enum's `.value` (a string) at every one of those fields, never a Python Enum repr

#### Scenario: IO error propagates to caller

- GIVEN a path that cannot be written
- WHEN `JsonReportAdapter.export(report_input, path)` is called
- THEN the underlying `OSError` propagates; `@generic_error_handler` on the use case wraps it as `SrcGenericError`

---

### Requirement: JsonReportWiring Factory

`JsonReportWiring.create_use_case()` MUST instantiate `JsonReportAdapter()` with no settings and return an `ExportReportUseCase` wired with it. It MUST reuse the existing `ExportReportUseCase` class unchanged — no new use-case class is introduced for JSON.

#### Scenario: Wiring returns a fully wired JSON use case

- GIVEN `JsonReportWiring()`
- WHEN `create_use_case()` is called
- THEN it returns an `ExportReportUseCase` instance whose port is a `JsonReportAdapter`
- AND the returned object's class is exactly `ExportReportUseCase`, the same class `ExportReportWiring().create_use_case()` returns

---

### Requirement: main.py save_json_report Uses the Hexagonal JSON Use Case

`SilvinaEditorialAssistant.save_json_report` MUST call the JSON-wired `ExportReportUseCase` with `self._last_report_input`, replacing the previous manual `json.dump()` call. `main.py` MUST NOT define `_prepare_for_json` after this change.

#### Scenario: save_json_report delegates to the JSON use case

- GIVEN an initialized `SilvinaEditorialAssistant` with `self._last_report_input` set after `analyze_document()`
- WHEN `save_json_report(analysis_results, output_path)` is called
- THEN the JSON-wired `ExportReportUseCase.execute` is invoked with `report_input=self._last_report_input` and `output_path=output_path`

#### Scenario: _prepare_for_json no longer exists

- GIVEN the updated `main.py` source
- WHEN `SilvinaEditorialAssistant` is inspected for a `_prepare_for_json` attribute
- THEN no such method is defined

---

## Constraints

| Constraint | Detail |
|------------|--------|
| Zero existing file modifications | 15 new files only; `presentation/word_exporter.py` stays untouched |
| Coexistence invariant | No `src/` file imports from `presentation/`; both layers coexist until Slice 16 |
| Callers out of scope | `main.py` and `gradio_app.py` continue using `WordExporter` until Slice 16 |
| Recommendations | `list[RecommendationDTO]` — typed and validated (TODO resolved in Slice 13) |
| Hard-fail at startup | `ReportExportUnavailable` raised in `__init__` — not deferred |
| Domain isolation | Domain imports nothing from infrastructure or application |
| One class per file | No multi-class modules |
| Test coverage | All new files covered by `unittest.TestCase` tests following port/fake/integration pattern |
