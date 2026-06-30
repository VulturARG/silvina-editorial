# Design: export-report (Slice 12 — Hexagonal Migration)

## Technical Approach

Wrap `WordExporter` logic in a typed port/adapter pair following the pattern established by Slices 9–11. The monolithic `Dict[str, Any]` interface becomes `ReportInputDTO` (frozen dataclass, typed fields), a `ReportExportPort` ABC gates the domain boundary, and `DocxReportAdapter` owns all 14 private DOCX-rendering methods. Wiring injects the logo path at startup; hard-fail if python-docx absent.

## Architecture Decisions

| Decision | Choice | Rejected | Rationale |
|----------|--------|----------|-----------|
| New DTO vs. extend `AnalysisResultDTO` | New `ReportInputDTO` | Add `grammar` + `apa_validation` + `recommendations` to `AnalysisResultDTO` | `AnalysisResultDTO` is an output aggregate with a `to_dict()` legacy contract; adding report-specific fields violates SRP and risks breaking callers. `ReportInputDTO` is a dedicated view-model for export. |
| Hard-fail vs. graceful degradation on missing python-docx | Hard-fail in `__init__`: raise `ReportExportUnavailable` | Return `False`; skip export silently | A report export system that silently produces nothing is worse than one that refuses to start. Hard-fail at wiring time surfaces the dependency problem before any user action. |
| All 14 private methods stay in adapter | Keep in `DocxReportAdapter` | Extract sub-services (title builder, header builder, etc.) | Each method is 10–30 lines with no independent reuse need. Sub-services would add indirection with no testability benefit. Mock strategy patches at Document level, not per-method. |
| `bool` return contract on `export()` | Raise on error (via `@generic_error_handler`); return `True` on success | Return `False` on error (legacy `WordExporter` pattern) | `False` is unactionable — the caller cannot distinguish "disk full" from "bad input". `@generic_error_handler` wraps unexpected exceptions to `SrcGenericError` and re-raises `SrcBaseWarning` as-is; callers get structured exceptions. |

## Data Flow

```
ExportReportWiring.create_use_case()
  └── DocxReportAdapter(logo_path=resolved_path)     ← DOCX_AVAILABLE guard
         ↓ implements
    ReportExportPort.export(report_input, path)
         ↑ called by
  ExportReportUseCase.execute(report_input, path)  @generic_error_handler
         ↑ called by future Slice 16 presenter
```

## File Changes

| File | Action | Notes |
|------|--------|-------|
| `src/domain/report/__init__.py` | Create | Empty package marker |
| `src/domain/report/report_export_port.py` | Create | `ReportExportPort(ABC)` |
| `src/domain/dtos/report_input_dto.py` | Create | `ReportInputDTO` frozen dataclass |
| `src/domain/exceptions/report_errors.py` | Create | `ReportExportUnavailable(SrcBaseWarning)` |
| `src/domain/tests/report/__init__.py` | Create | Empty package marker |
| `src/domain/tests/report/fake_report_export_port.py` | Create | `FakeReportExportPort` |
| `src/domain/tests/report/test_report_export_port.py` | Create | Port contract test |
| `src/application/export_report_use_case.py` | Create | `ExportReportUseCase` |
| `src/application/tests/test_export_report_use_case.py` | Create | Use case unit tests |
| `src/infrastructure/adapters/report/__init__.py` | Create | Empty package marker |
| `src/infrastructure/adapters/report/docx_report_adapter.py` | Create | `DocxReportAdapter` |
| `src/infrastructure/wirings/export_report_wiring.py` | Create | `ExportReportWiring` |
| `src/infrastructure/tests/adapters/report/__init__.py` | Create | Empty package marker |
| `src/infrastructure/tests/adapters/report/test_docx_report_adapter.py` | Create | Adapter integration tests |
| `src/infrastructure/tests/test_export_report_wiring.py` | Create | Wiring integration test |

## Interfaces / Contracts

### `ReportExportPort`

```python
class ReportExportPort(ABC):
    @abstractmethod
    def export(self, report_input: ReportInputDTO, path: str) -> bool: ...
```

### `ReportInputDTO` — field-by-field

| Field | Type | Source in WordExporter dict |
|-------|------|-----------------------------|
| `filename` | `str` | `results['filename']` |
| `document_content` | `DocumentContentDTO` | `results['document_info']` (title, authors, word_count, char_count); `estimated_pages` derived as `word_count // 250` in adapter |
| `classification` | `ClassificationResultDTO` | `results['classification']`; adapter reads `.article_type.value.upper()` (dict key was `'category'`) |
| `quality` | `QualityResultDTO` | `results['quality_analysis']` (overall_score, dimension_scores) |
| `grammar` | `GrammarCheckResultDTO` | `results['quality_analysis']['gramatica']` — **promoted to first-class field**; adapter reads `.score`, `.feedback`, `.errors` |
| `structure` | `StructureValidationResultDTO` | `results['structure_validation']` |
| `citations` | `CitationAnalysisResultDTO` | `results['citations_analysis']` |
| `apa_validation` | `ApaValidationResultDTO` | `results['apa_validation']`; `apa_violations` count derived as `len(report_input.apa_validation.violations)` |
| `recommendations` | `list[dict]` | `results['recommendations']`; dict contract: `{'priority': str, 'message': str}`; `# TODO Slice 13: replace with list[RecommendationDTO]` |

`GrammarCheckResultDTO` confirmed present at `src/domain/dtos/grammar_check_result_dto.py` (Slice 10 output).

### `ReportExportUnavailable`

```python
class ReportExportUnavailable(SrcBaseWarning):
    MESSAGE = "The report export service is unavailable (python-docx not installed)."
```

### `ExportReportUseCase`

```python
class ExportReportUseCase:
    def __init__(self, report_export_port: ReportExportPort) -> None: ...
    @generic_error_handler
    def execute(self, report_input: ReportInputDTO, path: str) -> bool: ...
```

### `DocxReportAdapter` — module-level guard

```python
try:
    from docx import Document
    from docx.shared import Pt, RGBColor, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_ALIGN_VERTICAL
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
```

```python
class DocxReportAdapter(ReportExportPort):
    def __init__(self, logo_path: str | None = None) -> None:
        if not DOCX_AVAILABLE:
            raise ReportExportUnavailable()
        self._logo_path = logo_path

    @generic_error_handler
    def export(self, report_input: ReportInputDTO, path: str) -> bool: ...

    # 14 private methods (all adapt dict-access to DTO attribute access):
    def _add_title_page(self, doc, report_input: ReportInputDTO) -> None: ...
    def _add_header_logo(self, doc) -> None: ...          # uses self._logo_path
    def _add_page_numbers(self, doc) -> None: ...
    def _add_executive_summary(self, doc, report_input: ReportInputDTO) -> None: ...
    def _add_document_info(self, doc, report_input: ReportInputDTO) -> None: ...
    def _add_classification(self, doc, report_input: ReportInputDTO) -> None: ...
    def _add_quality_analysis(self, doc, report_input: ReportInputDTO) -> None: ...
    def _add_grammar_analysis(self, doc, report_input: ReportInputDTO) -> None: ...
    def _add_apa_validation(self, doc, report_input: ReportInputDTO) -> None: ...
    def _add_structure_validation(self, doc, report_input: ReportInputDTO) -> None: ...
    def _add_citations_analysis(self, doc, report_input: ReportInputDTO) -> None: ...
    def _add_recommendations(self, doc, report_input: ReportInputDTO) -> None: ...
    def _add_footer(self, doc) -> None: ...
    def _determine_publishability(self, report_input: ReportInputDTO) -> tuple[bool, str]: ...
```

**Key DTO-to-dict translation notes for adapter implementation:**
- `_add_classification`: `classification['category']` → `report_input.classification.article_type`
- `_add_grammar_analysis`: reads `report_input.grammar` (not `report_input.quality.dimension_scores['gramatica']`)
- `_add_executive_summary` + `_determine_publishability`: `apa_violations` → `len(report_input.apa_validation.violations)`
- `_add_apa_validation`: `v['citation']` → `v.citation_text`; `v['error_type']` → `v.error_type` (ApaErrorType enum, hashable key); `err.get('correction')` → `err.correction` (always present, never None)
- `_add_document_info`: `info['estimated_pages']` → `report_input.document_content.word_count // 250`

### `ExportReportWiring`

```python
class ExportReportWiring:
    def create_use_case(self) -> ExportReportUseCase:
        logo_path = self._resolve_logo_path()
        return ExportReportUseCase(
            report_export_port=DocxReportAdapter(logo_path=str(logo_path) if logo_path.exists() else None)
        )

    def _resolve_logo_path(self) -> Path:
        # src/infrastructure/wirings/ → parents[3] = project root
        return Path(__file__).resolve().parents[3] / "assets" / "logo.jpg"
```

`DocxReportAdapter.__init__` raises `ReportExportUnavailable` if python-docx is absent — failure propagates from `create_use_case()`.

## Import Dependency Graph

```
domain/exceptions/report_errors.py
  ← domain/report/report_export_port.py   (imports ReportInputDTO)
  ← domain/dtos/report_input_dto.py       (imports 7 existing DTOs — all domain-only)
  ← application/export_report_use_case.py (imports port + DTO + decorator)
  ← infrastructure/adapters/report/docx_report_adapter.py
      (imports port + DTO + exception + decorator; docx imports guarded)
  ← infrastructure/wirings/export_report_wiring.py
      (imports use case + adapter)
```

No circular imports. Domain imports nothing from application or infrastructure.

## Testing Strategy

| Layer | What | Approach |
|-------|------|----------|
| Domain — exception | `ReportExportUnavailable` carries correct `MESSAGE`; `isinstance(SrcBaseWarning)` | Direct instantiation |
| Domain — DTO | `ReportInputDTO` is frozen; all 9 fields accepted | Frozen dataclass instantiation test |
| Domain — port | ABC cannot be instantiated directly; `FakeReportExportPort` satisfies contract | `with self.assertRaises(TypeError)` |
| Application | `execute()` delegates to port; returns port result; raises when port raises | `FakeReportExportPort` configured for True / False / raise |
| Adapter — availability | `__init__` raises `ReportExportUnavailable` when `DOCX_AVAILABLE=False` | Patch `docx_report_adapter.DOCX_AVAILABLE = False` |
| Adapter — export() | All 14 `_add_*` methods called; `doc.save()` called with correct path; returns `True` | `patch('...docx_report_adapter.Document')` → MagicMock; assert calls on mock instance |
| Adapter — equivalence | `.docx` output has same section headings as `WordExporter` | Create real `ReportInputDTO`, call both, open with `python-docx`, compare heading texts |
| Wiring | `create_use_case()` returns `ExportReportUseCase`; port is `DocxReportAdapter` | `isinstance` checks |

### `FakeReportExportPort`

```python
class FakeReportExportPort(ReportExportPort):
    def __init__(self, return_value: bool = True, raise_error: Exception | None = None):
        self._return_value = return_value
        self._raise_error = raise_error

    def export(self, report_input: ReportInputDTO, path: str) -> bool:
        if self._raise_error:
            raise self._raise_error
        return self._return_value
```

## Migration / Rollout

No migration required. `presentation/word_exporter.py` remains untouched. Zero files modified in this slice. Both classes coexist until Slice 16 removes `presentation/`.

## Open Questions

- [ ] `_add_apa_validation` groups violations by `error_type` but displays hardcoded "CITACIÓN INCORRECTA" — confirm this is acceptable for functional equivalence or if `error_type.value` should appear in the heading.
- [ ] Functional equivalence test: automated (parse both `.docx` outputs and compare headings) or manual checklist before merge? Proposal allows either; tasks phase should specify.
