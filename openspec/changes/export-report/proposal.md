# Proposal: export-report (Slice 12 — Hexagonal Migration)

**Change name**: export-report
**Slice**: 12 of N (incremental hexagonal migration)
**Date**: 2026-06-29
**Status**: proposed

---

## 1. Intent

### Problem

`presentation/word_exporter.py` (505 lines) exposes `WordExporter` as a monolithic class
with one public method `export_to_word(analysis_results: Dict[str, Any], output_path: str) -> bool`
that accepts an untyped dict. There is no port abstraction, no dependency injection, and no
path to unit-test the export logic without a real python-docx Document. The DOCX generation
concern is trapped in the `presentation/` layer, breaking the hexagonal boundary.

No caller in `src/` can request a report export without reaching outside the hexagonal
perimeter. The adapter shape, logo path, and availability guard are all implicit inside
`WordExporter.__init__` rather than being infrastructure concerns injected at wiring time.

### Why now

Slice 12 follows the rhythm established by Slices 9–11: the port/adapter/wiring/fake-double
pattern is stable, the DTO ecosystem covers all input fields (with one typed placeholder),
and the adapter complexity (13 private docx methods) is bounded and self-contained.
Completing this slice makes report export testable in isolation and prepares the wiring
layer for Slice 13 (RecommendationDTO) and Slice 16 (presentation/ cleanup).

### Success criteria

- A caller in `src/` can invoke `ExportReportUseCase.execute(report_input, path)` and
  receive a `bool` without importing anything from `presentation/`.
- `DocxReportAdapter.__init__` raises `ReportExportUnavailable` immediately if python-docx
  is not installed; the system does NOT start without it (hard-fail at wiring time).
- All new code is covered by `unittest.TestCase` tests following the established
  port/fake-double/integration pattern.
- The generated `.docx` output is **functionally equivalent** to what `WordExporter`
  currently produces: same sections, same content, same structure — verified by a
  comparison test or manual review before merging.
- The legacy `presentation/word_exporter.py` remains untouched; system works end-to-end
  (coexistence invariant).

---

## 2. Scope

### In scope — Files to create (15 new files, 0 modified)

**Domain — port**
- `src/domain/report/__init__.py`
- `src/domain/report/report_export_port.py`
  `ReportExportPort(ABC)` — single abstract method `export(report_input: ReportInputDTO, path: str) -> bool`

**Domain — DTO**
- `src/domain/dtos/report_input_dto.py`
  `ReportInputDTO` — frozen dataclass: `filename: str`, `document_content: DocumentContentDTO`,
  `classification: ClassificationResultDTO`, `quality: QualityResultDTO`,
  `grammar: GrammarCheckResultDTO`, `structure: StructureValidationResultDTO`,
  `citations: CitationAnalysisResultDTO`, `apa_validation: ApaValidationResultDTO`,
  `recommendations: list[dict]`  ← placeholder until Slice 13 defines `RecommendationDTO`

**Domain — exceptions**
- `src/domain/exceptions/report_errors.py`
  `ReportExportUnavailable(SrcBaseWarning)` with `MESSAGE = "The report export service is unavailable (python-docx not installed)."`

**Domain — tests**
- `src/domain/tests/report/__init__.py`
- `src/domain/tests/report/fake_report_export_port.py`
  `FakeReportExportPort(ReportExportPort)` — returns configurable bool; optional raise
- `src/domain/tests/report/test_report_export_port.py`
  Contract test: verifies ABC method signature and that `FakeReportExportPort` satisfies the port

**Application — use case**
- `src/application/export_report_use_case.py`
  `ExportReportUseCase` — `__init__(port: ReportExportPort)`;
  `execute(report_input: ReportInputDTO, path: str) -> bool`; `@generic_error_handler` on `execute`

**Application — tests**
- `src/application/tests/test_export_report_use_case.py`
  Unit tests using `FakeReportExportPort`

**Infrastructure — adapter**
- `src/infrastructure/adapters/report/__init__.py`
- `src/infrastructure/adapters/report/docx_report_adapter.py`
  `DocxReportAdapter(ReportExportPort)` — `__init__(logo_path: str | None = None)` raises
  `ReportExportUnavailable` if python-docx not installed; module-level `DOCX_AVAILABLE` guard;
  `@generic_error_handler` on `export()`; all 13 private rendering methods stay private;
  `estimated_pages` derived as `report_input.document_content.word_count // 250`;
  `apa_violations` count derived as `len(report_input.apa_validation.violations)`;
  `article_type` read as `report_input.classification.article_type.value.upper()`

**Infrastructure — wiring**
- `src/infrastructure/wirings/export_report_wiring.py`
  `ExportReportWiring.create_use_case() -> ExportReportUseCase`; resolves `logo_path`
  relative to project root at wiring time; raises `ReportExportUnavailable` at startup
  if python-docx is absent (hard-fail, system does not start)

**Infrastructure — tests**
- `src/infrastructure/tests/adapters/report/__init__.py`
- `src/infrastructure/tests/adapters/report/test_docx_report_adapter.py`
  Integration test with MagicMock python-docx Document; verifies all 13 section methods
  are called and `export()` returns `True`; includes functional equivalence comparison
  against `WordExporter` output (same section titles and content markers)
- `src/infrastructure/tests/test_export_report_wiring.py`
  Wiring integration test: instantiates `ExportReportWiring`, calls `create_use_case()`,
  asserts `isinstance(use_case, ExportReportUseCase)` and port attribute type

### Out of scope

- Any modification to `presentation/word_exporter.py` — kept alive for coexistence until Slice 16
- Updating `main.py` or `gradio_app.py` callers — they continue calling `WordExporter` directly until Slice 16
- `RecommendationDTO` definition — Slice 13 concern; `list[dict]` placeholder accepted with code comment
- Parameterizing language or section structure beyond current `WordExporter` behavior
- Wiring `ExportReportUseCase` into Gradio UI entry points — future integration step

---

## 3. Approach

### Architecture

```
[ReportInputDTO + path: str]
         |
         v
DocxReportAdapter ──implements──> ReportExportPort (ABC, domain/report/)
  __init__(logo_path=None): raises ReportExportUnavailable if python-docx absent
  export(report_input, path) -> bool  (@generic_error_handler)
    └── _add_title_page()
    └── _add_header_logo()          logo_path injected at construction
    └── _add_page_numbers()
    └── _add_executive_summary()
    └── _add_document_info()
    └── _add_classification()       reads article_type.value.upper()
    └── _add_quality_analysis()
    └── _add_grammar_analysis()
    └── _add_apa_validation()       derives count from len(apa_validation.violations)
    └── _add_structure_validation()
    └── _add_citations_analysis()
    └── _add_recommendations()      reads rec['priority'], rec['message'] from list[dict]
    └── _add_footer()
         |
         v
ExportReportUseCase.execute(report_input, path)
         └── _report_export_port.export(report_input, path)
         |
         v
ExportReportWiring.create_use_case()
         └── resolves logo_path relative to project root
         └── raises ReportExportUnavailable at startup if python-docx absent
```

**Port location**: `src/domain/report/` — entity-scoped, consistent with Slices 9–11.

**Error handling**: `DocxReportAdapter.__init__` raises `ReportExportUnavailable` directly
(not via `@generic_error_handler`) so the failure happens at construction time.
`@generic_error_handler` on `export()` handles runtime DOCX rendering errors.

**Logo path**: resolved at wiring time from project root, passed as constructor argument.
Adapter is fully testable without filesystem access (`logo_path=None` skips logo silently).

**DTO field note**: `recommendations: list[dict]` carries a code comment:
`# TODO Slice 13: replace with list[RecommendationDTO]`

### TDD order (strict TDD mode active)

1. Exception class + test (`ReportExportUnavailable`)
2. DTO + test (`ReportInputDTO`)
3. Port ABC + fake double + contract test
4. Use case tests (with fake) → use case implementation (RED → GREEN → REFACTOR)
5. Adapter tests (MagicMock + functional equivalence) → adapter implementation
6. Wiring test → wiring implementation

---

## 4. Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| `recommendations: list[dict]` diverges from Slice 13 DTO shape | Low | Slice 13 immediately follows; code comment makes the coupling explicit; adapter reads only `priority` + `message` keys |
| 13 private adapter methods make MagicMock tests verbose and brittle | Medium | Mirror pattern from `test_docx_eumic_adapter.py`; patch at Document level, not per-method; functional equivalence test at integration level |
| `article_type` vs. `category` field name mismatch in ClassificationResultDTO | Low | Exploration confirmed correct field is `article_type`; spec must enforce this |
| Functional equivalence test is manual or partial | Medium | Define explicit section checklist (title page, executive summary, 8 analysis sections, footer) in test; run once against real input before merge |
| Logo path breaks when project root changes | Low | Wiring resolves from `Path(__file__).parent` chain to project root; covered by wiring test |
| Hard-fail at startup may surprise developers without python-docx | Low | Document in README / wiring docstring; error message is explicit |

---

## 5. PR Shape

Single PR targeting `refactor/hexagonal-migration`.
- 15 new files, 0 modified files
- Estimated changed lines: ~350–430
- Budget risk: Medium — close to 400-line threshold but no chained PRs required given 0 modified files

---

## 6. Definition of Done

Per `docs/plan-migracion-hexagonal.md` §8 — a slice is done when all of the
following are checked:

- [ ] `ReportExportPort(ABC)` defined in `src/domain/report/` with `export()` signature
- [ ] `ReportInputDTO` (frozen dataclass) covers all 8 data fields; `recommendations` has `list[dict]` placeholder comment
- [ ] `ReportExportUnavailable(SrcBaseWarning)` defined with tests
- [ ] `ExportReportUseCase.execute()` tested with `FakeReportExportPort`; `@generic_error_handler` applied
- [ ] `DocxReportAdapter.__init__` raises `ReportExportUnavailable` at construction if python-docx absent
- [ ] `DocxReportAdapter.export()` produces a `.docx` with functionally equivalent sections to `WordExporter`
- [ ] Functional equivalence verified: same section titles/content in both outputs (comparison test or manual review)
- [ ] `ExportReportWiring.create_use_case()` returns fully wired instance; wiring integration test passes
- [ ] No imports from `presentation/` in any `src/` file
- [ ] Domain imports nothing from infrastructure or application (hexagonal invariant)
- [ ] No local imports; no wildcard imports; no `print()` statements
- [ ] One class per file
- [ ] `python -m pytest src/ -q` passes with all tests green
- [ ] `presentation/word_exporter.py` untouched; system works end-to-end

---

## 7. Dependencies

- `python-docx` — required at runtime; hard-fail at startup if absent
- `src/domain/exceptions/base_src_error.py` — `SrcBaseWarning` (exists)
- `src/domain/exceptions/decorators/generic_error_handler.py` — `@generic_error_handler` (exists)
- `src/domain/dtos/base_dto.py` — `BaseDTO` base class (exists)
- `src/domain/dtos/document_content_dto.py` — `DocumentContentDTO` (exists)
- `src/domain/dtos/classification_result_dto.py` — `ClassificationResultDTO` (exists)
- `src/domain/dtos/quality_result_dto.py` — `QualityResultDTO` (exists)
- `src/domain/dtos/grammar_check_result_dto.py` — `GrammarCheckResultDTO` (exists, Slice 10)
- `src/domain/dtos/structure_validation_result_dto.py` — `StructureValidationResultDTO` (exists)
- `src/domain/dtos/citation_analysis_result_dto.py` — `CitationAnalysisResultDTO` (exists)
- `src/domain/dtos/apa_validation_result_dto.py` — `ApaValidationResultDTO` (exists)
- `RecommendationDTO` — NOT yet defined; `list[dict]` placeholder until Slice 13
