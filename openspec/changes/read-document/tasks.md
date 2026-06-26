# SDD Tasks — read-document (Slice 5)

**Change**: read-document
**Phase**: tasks
**Status**: active
**TDD**: STRICT (RED → GREEN)
**Test runner**: `python -m pytest src/ tests/`

---

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~310 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Full slice: port, adapter, use case, wiring, tests, parity smoke test | PR 1 | All additive, no existing file touched; small enough for a single review |

---

## Phase 1 — SCAFFOLD (parallel, no tests)

### T-01 [SCAFFOLD] Create `src/domain/document/__init__.py` [x]
- Empty file, new entity package
- Spec ref: DocumentTextPort Contract

### T-02 [SCAFFOLD] Create `src/domain/tests/document/__init__.py` [x]
- Empty file
- Pre-condition: `src/domain/tests/__init__.py` already exists

### T-03 [SCAFFOLD] Create `src/infrastructure/adapters/document/__init__.py` [x]
- Empty file, new adapter package
- Pre-condition: `src/infrastructure/adapters/__init__.py` already exists

### T-04 [SCAFFOLD] Create `src/infrastructure/tests/adapters/document/__init__.py` [x]
- Empty file (create `src/infrastructure/tests/adapters/__init__.py` too if missing)
- Pre-condition: `src/infrastructure/tests/__init__.py` already exists

> T-01–T-04 are independent and can run in parallel. `src/application/tests/`, `src/infrastructure/wirings/`, `tests/smoke/` already exist — do NOT recreate.

---

## Phase 2 — DOMAIN PORT (sequential TDD loop)

### T-05 [RED] Write failing test for `DocumentTextPort` [x]
- File: `src/domain/tests/document/test_document_text_port.py`
- One `TestCase` class: `TestDocumentTextPort`
- Test methods:
  - `test_is_abstract_base_class`
  - `test_declares_exactly_one_abstract_method_read_paragraphs`
  - `test_module_has_no_docx_or_infrastructure_imports` — inspect source text for `import docx` / `src.infrastructure`
- Depends on: T-01, T-02

### T-06 [GREEN] Implement `DocumentTextPort` [x]
- File: `src/domain/document/document_text_port.py`
- `ABC` with one `@abstractmethod read_paragraphs(self, path: str) -> list[str]`
- Zero imports beyond `abc`
- Run: `python -m pytest src/domain/tests/document/test_document_text_port.py` → green
- Depends on: T-05

---

## Phase 3 — ADAPTER (sequential TDD loop)

### T-07 [RED] Write failing tests for `DocxTextAdapter` [x]
- File: `src/infrastructure/tests/adapters/document/test_docx_text_adapter.py`
- One `TestCase` class: `TestDocxTextAdapter`
- Test methods:
  - `test_strips_and_filters_empty_paragraphs` — fixture `docs/sample-documents/1. test_Científico.docx`
  - `test_preserves_paragraph_order`
  - `test_no_non_empty_paragraphs_returns_empty_list` — build minimal `.docx` via `python-docx` in `setUp`/temp dir
  - `test_missing_file_raises_document_not_found`
  - `test_corrupt_file_raises_document_unreadable` — write a temp `.docx`-named file with non-zip bytes
  - `test_valid_file_raises_no_exception`
- Depends on: T-03, T-04, T-06

### T-08 [GREEN] Implement `DocxTextAdapter` [x]
- File: `src/infrastructure/adapters/document/docx_text_adapter.py`
- `class DocxTextAdapter(DocumentTextPort)`, `@generic_error_handler`-decorated `read_paragraphs`
- `Path(path).exists()` check → `DocumentNotFound`; `try/except Exception` around `Document(path)` → `DocumentUnreadable` (`from exc`)
- List comprehension: strip + filter empty, preserve order
- Run: `python -m pytest src/infrastructure/tests/adapters/document/test_docx_text_adapter.py` → green
- Depends on: T-07

---

## Phase 4 — USE CASE (sequential TDD loop)

### T-09 [RED] Write failing tests for `ReadDocumentUseCase` [x]
- File: `src/application/tests/test_read_document_use_case.py`
- One `TestCase` class: `TestReadDocumentUseCase`
- Fake `DocumentTextPort` test double
- Test methods:
  - `test_execute_returns_ports_result_unchanged`
  - `test_execute_propagates_document_not_found_unchanged`
  - `test_module_does_not_import_document_content_dto`
- Depends on: T-06

### T-10 [GREEN] Implement `ReadDocumentUseCase` [x]
- File: `src/application/read_document_use_case.py`
- `__init__(self, port: DocumentTextPort)`, `execute(self, path: str) -> list[str]` → `return self._port.read_paragraphs(path)`
- No `DocumentContentDTO` import
- Run: `python -m pytest src/application/tests/test_read_document_use_case.py` → green
- Depends on: T-09

---

## Phase 5 — WIRING (sequential TDD loop)

### T-11 [RED] Write failing test for `ReadDocumentUseCaseWiring` [x]
- File: `src/infrastructure/tests/test_read_document_use_case_wiring.py`
- One `TestCase` class: `TestReadDocumentUseCaseWiring`
- Test methods:
  - `test_create_use_case_returns_read_document_use_case_backed_by_docx_text_adapter`
  - `test_docx_logic_confined_to_private_get_method` — inspect `create_use_case` source for absence of `docx`/`Document(`
- Depends on: T-08, T-10

### T-12 [GREEN] Implement `ReadDocumentUseCaseWiring` [x]
- File: `src/infrastructure/wirings/read_document_use_case_wiring.py`
- Instance method `create_use_case(self) -> ReadDocumentUseCase` + private `_get_document_text_port(self) -> DocumentTextPort` returning `DocxTextAdapter()`
- Run: `python -m pytest src/infrastructure/tests/test_read_document_use_case_wiring.py` → green
- Depends on: T-11

---

## Phase 6 — PARITY SMOKE TEST

### T-13 [RED→GREEN] Write and pass parity smoke test [x]
- File: `tests/smoke/test_read_document_parity.py`
- Same shape as `tests/smoke/test_validate_structure_parity.py`
- Parametrize over the three sample docs in `docs/sample-documents/`
- Assert `ReadDocumentUseCaseWiring().create_use_case().execute(path) == WordReader.read_word_document(path)` element-for-element
- Depends on: T-12 (already green by construction — both sides are faithful ports; run to confirm)

---

## Phase 7 — VERIFICATION

### T-14 [VERIFY] Run full test suite — zero regressions [x]
- Command: `python -m pytest src/ tests/`
- Assertions:
  - All pre-existing tests pass unchanged
  - `data_access/word_reader.py` untouched (legacy not modified)
  - No new exception types created (`DocumentNotFound`/`DocumentUnreadable` from Slice 1 reused)
  - `ReadDocumentUseCase` not wired into `main.py`/`gradio_app.py` (out of scope, Slice 14)
- Depends on: T-13

---

## Dependency Graph

```
T-01 ──► T-05 ──► T-06 ──┐
T-02 ────────────────────┤
T-03 ──┐                 ├──► T-07 ──► T-08 ──┐
T-04 ──┘                 │                    ├──► T-11 ──► T-12 ──► T-13 ──► T-14
                          └──► T-09 ──► T-10 ──┘
```

**Parallel groups:**
- Group A (scaffold): T-01, T-02, T-03, T-04

---

## Files Summary

### New files to create (10)

| Path | Phase |
|------|-------|
| `src/domain/document/__init__.py` | T-01 |
| `src/domain/tests/document/__init__.py` | T-02 |
| `src/infrastructure/adapters/document/__init__.py` | T-03 |
| `src/infrastructure/tests/adapters/document/__init__.py` | T-04 |
| `src/domain/tests/document/test_document_text_port.py` | T-05 |
| `src/domain/document/document_text_port.py` | T-06 |
| `src/infrastructure/tests/adapters/document/test_docx_text_adapter.py` | T-07 |
| `src/infrastructure/adapters/document/docx_text_adapter.py` | T-08 |
| `src/application/tests/test_read_document_use_case.py` | T-09 |
| `src/application/read_document_use_case.py` | T-10 |
| `src/infrastructure/tests/test_read_document_use_case_wiring.py` | T-11 |
| `src/infrastructure/wirings/read_document_use_case_wiring.py` | T-12 |
| `tests/smoke/test_read_document_parity.py` | T-13 |

### Files that already exist — DO NOT recreate

| Path | Verified |
|------|---------|
| `src/application/tests/__init__.py` | exists |
| `src/infrastructure/wirings/__init__.py` | exists |
| `src/infrastructure/tests/__init__.py` | exists |
| `src/infrastructure/adapters/__init__.py` | exists |
| `tests/smoke/__init__.py` | exists |
| `src/domain/exceptions/document_errors.py` (`DocumentNotFound`, `DocumentUnreadable`) | exists |

No existing file is modified or deleted.

---

## Review Workload Forecast Detail

| Category | Files | Est. Lines |
|----------|-------|------------|
| Scaffold `__init__.py` | 4 | ~4 |
| `test_document_text_port.py` | 1 | ~25 |
| `document_text_port.py` | 1 | ~10 |
| `test_docx_text_adapter.py` | 1 | ~70 |
| `docx_text_adapter.py` | 1 | ~20 |
| `test_read_document_use_case.py` | 1 | ~30 |
| `read_document_use_case.py` | 1 | ~10 |
| `test_read_document_use_case_wiring.py` | 1 | ~25 |
| `read_document_use_case_wiring.py` | 1 | ~12 |
| `test_read_document_parity.py` | 1 | ~35 |
| **Total** | **13** | **~241 lines** |

No chained PRs needed for this slice.
