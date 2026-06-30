# Tasks: export-report (Slice 12 — Hexagonal Migration)

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 440–480 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1: Domain + Application → PR 2: Infrastructure |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: pending
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Domain + Application layers (exception, DTO, port, fake, use case + tests) | PR 1 | Base: `refactor/hexagonal-migration`; ~160–180 lines; fully testable in isolation |
| 2 | Infrastructure layer (adapter + wiring + tests) | PR 2 | Base: PR 1 branch; ~280–300 lines; depends on PR 1 domain types |

---

## Phase 1: Domain Foundation (Strict TDD — RED → GREEN)

- [ ] 1.1 [RED] Create `src/domain/tests/report/__init__.py` (empty) and `src/domain/tests/report/test_report_export_port.py` with failing tests:
  - `ReportExportUnavailable.MESSAGE` equals `"The report export service is unavailable (python-docx not installed)."` and `isinstance(SrcBaseWarning)` holds
  - `ReportInputDTO` constructed with all 9 fields; reassigning any field raises `FrozenInstanceError`
  - `ReportExportPort()` raises `TypeError` (ABC guard)
  - `FakeReportExportPort` satisfies port contract (no `TypeError`)
- [ ] 1.2 [GREEN] Create `src/domain/exceptions/report_errors.py` — `ReportExportUnavailable(SrcBaseWarning)` with `MESSAGE` constant; run relevant tests GREEN
- [ ] 1.3 [GREEN] Create `src/domain/dtos/report_input_dto.py` — frozen dataclass; 9 fields: `filename: str`, `document_content: DocumentContentDTO`, `classification: ClassificationResultDTO`, `quality: QualityResultDTO`, `grammar: GrammarCheckResultDTO` (top-level, not nested under quality), `structure: StructureValidationResultDTO`, `citations: CitationAnalysisResultDTO`, `apa_validation: ApaValidationResultDTO`, `recommendations: list[dict]` with inline comment `# TODO Slice 13: replace with list[RecommendationDTO]`; run tests GREEN
- [ ] 1.4 [GREEN] Create `src/domain/report/__init__.py` (empty) and `src/domain/report/report_export_port.py` — `ReportExportPort(ABC)` with single abstract method `export(self, report_input: ReportInputDTO, path: str) -> bool`; domain imports nothing from application or infrastructure; run tests GREEN
- [ ] 1.5 [GREEN] Create `src/domain/tests/report/fake_report_export_port.py` — `FakeReportExportPort(ReportExportPort)`: `__init__(return_value: bool = True, raise_error: Exception | None = None)`; `export()` raises if `raise_error` set, else returns `return_value`; run full domain suite GREEN

## Phase 2: Application Layer (Strict TDD — RED → GREEN)

- [ ] 2.1 [RED] Create `src/application/tests/test_export_report_use_case.py` with failing tests:
  - `execute()` delegates to port and returns `True`
  - `execute()` delegates to port and returns `False`
  - `execute()` propagates `ReportExportUnavailable` from port
  - `@generic_error_handler` wraps unexpected exceptions to `SrcGenericError`
- [ ] 2.2 [GREEN] Create `src/application/export_report_use_case.py` — `ExportReportUseCase.__init__(report_export_port: ReportExportPort)`; apply `@generic_error_handler` on `execute(self, report_input: ReportInputDTO, path: str) -> bool` which calls `self._report_export_port.export(report_input, path)`; run tests GREEN

## Phase 3: Infrastructure — Adapter (Strict TDD — RED → GREEN)

- [ ] 3.1 [RED] Create `src/infrastructure/tests/adapters/report/__init__.py` (empty) and `src/infrastructure/tests/adapters/report/test_docx_report_adapter.py` with failing tests:
  - Patching `DOCX_AVAILABLE = False` → `__init__` raises `ReportExportUnavailable`
  - Patching `DOCX_AVAILABLE = True` → `__init__` succeeds with `logo_path=None`
  - `export()` calls all 14 `_add_*` methods on the mock `Document` instance; `doc.save(path)` is called; returns `True`
  - `_determine_publishability` reads `len(report_input.apa_validation.violations)` (not a dict key `apa_violations`)
  - `_add_grammar_analysis` reads `report_input.grammar` directly (not `report_input.quality.dimension_scores['gramatica']`)
  - `_add_apa_validation` reads `violation.citation_text` (not `v['citation']`) and `violation.error_type` (not `v['error_type']`)
  - `_add_classification` reads `report_input.classification.article_type.value.upper()` (not `classification['category']`)
  - `_add_document_info` derives `estimated_pages` as `report_input.document_content.word_count // 250`
  - Functional equivalence scenario: `.docx` output contains all 11 section headings matching `WordExporter` (title page, executive summary, document info, classification, quality analysis, grammar, APA validation, structure validation, citations, recommendations, footer)
- [ ] 3.2 [GREEN] Create `src/infrastructure/adapters/report/__init__.py` (empty)
- [ ] 3.3 [GREEN] Create `src/infrastructure/adapters/report/docx_report_adapter.py`:
  - Module-level guard: `try: from docx import Document, ...; DOCX_AVAILABLE = True` / `except ImportError: DOCX_AVAILABLE = False`
  - `DocxReportAdapter(ReportExportPort).__init__(logo_path: str | None = None)`: raises `ReportExportUnavailable` immediately if not `DOCX_AVAILABLE`; stores `self._logo_path = logo_path`
  - Apply `@generic_error_handler` on `export(self, report_input: ReportInputDTO, path: str) -> bool`; call all 14 private methods; `doc.save(path)`; return `True`
  - Migrate all 14 private methods from `WordExporter`: `_add_title_page`, `_add_header_logo`, `_add_page_numbers`, `_add_executive_summary`, `_add_document_info`, `_add_classification`, `_add_quality_analysis`, `_add_grammar_analysis`, `_add_apa_validation`, `_add_structure_validation`, `_add_citations_analysis`, `_add_recommendations`, `_add_footer`, `_determine_publishability`
  - Replace every dict access with DTO attribute access per field translation table in design
  - Run tests GREEN

## Phase 4: Infrastructure — Wiring (Strict TDD — RED → GREEN)

- [ ] 4.1 [RED] Create `src/infrastructure/tests/test_export_report_wiring.py` with failing tests:
  - `ExportReportWiring().create_use_case()` returns `ExportReportUseCase` instance
  - Port attribute on returned use case is `DocxReportAdapter` instance
  - When `DOCX_AVAILABLE = False`, `create_use_case()` propagates `ReportExportUnavailable`
- [ ] 4.2 [GREEN] Create `src/infrastructure/wirings/export_report_wiring.py` — `ExportReportWiring.create_use_case() -> ExportReportUseCase`: resolves logo via `Path(__file__).resolve().parents[3] / "assets" / "logo.jpg"`; passes `str(logo_path)` if `logo_path.exists()` else `None`; instantiates `DocxReportAdapter(logo_path=...)`; returns `ExportReportUseCase(report_export_port=adapter)`; run tests GREEN

## Phase 5: Verification

- [ ] 5.1 Run `python -m pytest src/ -q` — all tests GREEN, zero regressions in existing suite
- [ ] 5.2 Coexistence: confirm `presentation/word_exporter.py` is untouched; no `src/` file imports anything from `presentation/`
- [ ] 5.3 Hexagonal invariant: no file under `src/domain/` imports from `src/application/` or `src/infrastructure/`
- [ ] 5.4 Functional equivalence confirmed: adapter `.docx` output headings match `WordExporter` output for all 11 sections (automated comparison or manual checklist before merge)
