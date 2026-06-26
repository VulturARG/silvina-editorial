# Design: read-document (Slice 5)

## Technical Approach

Faithful port/adapter wrap of `WordReader.read_word_document()`. The port
(`DocumentTextPort`, already fixed by spec at `src/domain/document/document_text_port.py`)
declares `read_paragraphs(path: str) -> list[str]`. A new `python-docx` adapter implements
it, mapping `python-docx`'s own failure modes to the existing `DocumentNotFound` /
`DocumentUnreadable` domain exceptions explicitly, before `@generic_error_handler` ever
sees them. `ReadDocumentUseCase` is a one-line pass-through. Wiring follows the established
instance-based factory pattern (`create_use_case()` + private `_get_*()`).

## Architecture Decisions

### Decision: Adapter location and naming

**Choice**: `src/infrastructure/adapters/document/docx_text_adapter.py`, class
`DocxTextAdapter`.
**Alternatives considered**: (a) flat file `src/infrastructure/adapters/docx_text_adapter.py`
with no subfolder; (b) name `WordDocumentAdapter` or `PythonDocxTextAdapter`.
**Rationale**: Follows the existing `adapters/<entity>/` precedent
(`adapters/llm_generator/ollama_generator_adapter.py`) — `document` is the entity folder the
port already lives under (`domain/document/`), keeping port and adapter folder names aligned.
`DocxTextAdapter` matches the `Docx{PortConcern}Adapter` naming convention already used by the
plan's other python-docx adapters (`DocxCitationAdapter`, `DocxReferenceAdapter`,
`DocxReportAdapter`, `DocxEumicAdapter` — docs/plan-migracion-hexagonal.md §4.3). The plan's
table row for this specific slice said `PythonDocxTextAdapter`, but that is inconsistent with
its four siblings wrapping the same library and is corrected here to `DocxTextAdapter`; the
plan table is updated to match.

### Decision: Exception mapping at the adapter boundary

**Choice**: The adapter explicitly checks file existence with `pathlib.Path.exists()` before
calling `docx.Document(path)`, raising `DocumentNotFound` itself (no dependency on
`python-docx`'s own error for the not-found case). It wraps the `docx.Document(path)` call in
a `try/except Exception` that re-raises as `DocumentUnreadable`. `@generic_error_handler`
still decorates the method as a safety net for anything unexpected, but since it already
re-raises `BaseSrcError` subclasses untouched (see `generic_error_handler.py:32-38`), the
explicit catches are what actually produce the typed exceptions — the decorator does not
infer exception type from a generic `Exception`, it only wraps non-`BaseSrcError` failures
into `SrcGenericError`.
**Alternatives considered**: (a) rely solely on `@generic_error_handler` to wrap any failure
into `SrcGenericError` and let callers inspect `__cause__`; (b) catch `python-docx`'s internal
`PackageNotFoundError`/`opc.exceptions` types by name and remap.
**Rationale**: (a) violates the spec's explicit requirement that bare built-ins/`SrcGenericError`
must not leak — callers need `DocumentNotFound`/`DocumentUnreadable` specifically. (b) is more
precise but couples the adapter to `python-docx`'s internal exception taxonomy, which is not
guaranteed stable across versions; a broad `except Exception` after a successful existence
check is safe because the only remaining failure mode at that point is "file exists but
python-docx could not parse it" — exactly what `DocumentUnreadable` means.

### Decision: Use case and wiring file locations

**Choice**: `src/application/read_document_use_case.py` (class `ReadDocumentUseCase`);
`src/infrastructure/wirings/read_document_use_case_wiring.py` (class
`ReadDocumentUseCaseWiring`).
**Alternatives considered**: None — both paths are already dictated by the spec
(Requirements "ReadDocumentUseCase Thin Pass-Through" and "Wiring Follows the Instance-Based
Factory Pattern") and match the flat `src/application/*_use_case.py` /
`src/infrastructure/wirings/*_use_case_wiring.py` precedent used by every prior slice.
**Rationale**: Consistency; no new decision needed beyond confirming the precedent.

## Data Flow

    ReadDocumentUseCaseWiring.create_use_case()
            │
            ▼
    ReadDocumentUseCase(port=DocxTextAdapter())
            │  .execute(path)
            ▼
    DocxTextAdapter.read_paragraphs(path)
            │
            ├─ Path(path).exists()? ──No──→ raise DocumentNotFound
            │
            ▼ Yes
        docx.Document(path)  ──raises any Exception──→ raise DocumentUnreadable
            │
            ▼
    iterate doc.paragraphs → strip() → filter empty → list[str]
            │
            ▼
    returned unchanged through UseCase.execute() to caller

## File Changes

| File | Action | Description |
|------|--------|--------------|
| `src/domain/document/__init__.py` | Create | New entity package |
| `src/domain/document/document_text_port.py` | Create | `DocumentTextPort` ABC, one abstract method |
| `src/infrastructure/adapters/document/__init__.py` | Create | New adapter package |
| `src/infrastructure/adapters/document/docx_text_adapter.py` | Create | `DocxTextAdapter` |
| `src/application/read_document_use_case.py` | Create | `ReadDocumentUseCase` |
| `src/infrastructure/wirings/read_document_use_case_wiring.py` | Create | `ReadDocumentUseCaseWiring` |
| `src/domain/tests/document/test_document_text_port.py` | Create | Port contract test (ABC, one method, no infra imports) |
| `src/infrastructure/tests/adapters/document/test_docx_text_adapter.py` | Create | Adapter behavior + exception mapping tests |
| `src/application/tests/test_read_document_use_case.py` | Create | Pass-through + exception propagation test, fake port |
| `tests/smoke/test_read_document_parity.py` | Create | Parity vs. legacy `WordReader.read_word_document()`, following `test_validate_structure_parity.py` pattern |

No existing file is modified or deleted.

## Interfaces / Contracts

```python
# src/domain/document/document_text_port.py
from abc import ABC, abstractmethod

class DocumentTextPort(ABC):
    @abstractmethod
    def read_paragraphs(self, path: str) -> list[str]: ...
```

```python
# src/infrastructure/adapters/document/docx_text_adapter.py
from pathlib import Path
from docx import Document

from src.domain.document.document_text_port import DocumentTextPort
from src.domain.exceptions.decorators.generic_error_handler import generic_error_handler
from src.domain.exceptions.document_errors import DocumentNotFound, DocumentUnreadable

class DocxTextAdapter(DocumentTextPort):
    @generic_error_handler
    def read_paragraphs(self, path: str) -> list[str]:
        if not Path(path).exists():
            raise DocumentNotFound()
        try:
            document = Document(path)
        except Exception as exc:
            raise DocumentUnreadable() from exc
        return [text for p in document.paragraphs if (text := p.text.strip())]
```

```python
# src/application/read_document_use_case.py
from src.domain.document.document_text_port import DocumentTextPort

class ReadDocumentUseCase:
    def __init__(self, port: DocumentTextPort) -> None:
        self._port = port

    def execute(self, path: str) -> list[str]:
        return self._port.read_paragraphs(path)
```

```python
# src/infrastructure/wirings/read_document_use_case_wiring.py
from src.application.read_document_use_case import ReadDocumentUseCase
from src.domain.document.document_text_port import DocumentTextPort
from src.infrastructure.adapters.document.docx_text_adapter import DocxTextAdapter

class ReadDocumentUseCaseWiring:
    def create_use_case(self) -> ReadDocumentUseCase:
        return ReadDocumentUseCase(port=self._get_document_text_port())

    def _get_document_text_port(self) -> DocumentTextPort:
        return DocxTextAdapter()
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Domain (port) | ABC shape, no infra imports | Reflection on `DocumentTextPort` |
| Adapter | Strip/filter/order behavior, `DocumentNotFound`, `DocumentUnreadable` | Real/fixture `.docx` files in `docs/sample-documents/` + a corrupt-file fixture |
| Application | Pass-through, exception propagation, no `DocumentContentDTO` import | Fake `DocumentTextPort` test double |
| Smoke (parity) | Legacy vs. new equal output on real sample docs | `tests/smoke/test_read_document_parity.py`, same shape as `test_validate_structure_parity.py` |

## Migration / Rollout

No migration required. All files are additive; nothing currently calls the new code path.
Legacy `data_access/word_reader.py` stays untouched and in production use until Slice 14.

## Open Questions

None — both decisions deferred by the spec (adapter naming/location, exception wiring) are
resolved above.
