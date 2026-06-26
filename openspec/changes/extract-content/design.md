# Design: extract-content

## Technical Approach

Two-port hexagonal slice: `ContentExtractionPort` owns heuristic extraction from paragraphs (no I/O), `CharacterCountPort` owns win32com-based counting (I/O, Windows-only). `ExtractContentUseCase` orchestrates both ports, merges counts, and returns a single frozen `DocumentContentDTO`. The count port returns `None` for all degradation paths (win32com unavailable or COM failure after retry) — the use case checks the return value, never catches exceptions for flow control. All vocabulary constants that were inline in `ContentExtractor` are promoted to `extraction_vocabulary.py` so the adapter contains only structural logic.

## Architecture Decisions

### Decision: Two ports instead of one

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Single port `extract(paragraphs, path)` that calls COM internally | Simpler wiring; violates SRP — extraction + I/O in same port | Rejected |
| Two ports: extraction (pure) + count (I/O) | Correct SRP; extraction port is testable without file system | **Chosen** |
| Three ports (separate title/author/sections ports) | Over-engineered; no independent consumers | Rejected |

### Decision: Count port returns None for all degradation paths

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Raise `SrcBaseWarning` on COM failure; use case catches it | Uses exceptions for flow control — antipattern | Rejected |
| Raise `SrcGenericError` on COM failure | Would propagate to caller as unhandled error | Rejected |
| Return `None` for both "unavailable" and "COM failure"; log via `logger.warning()` | `None` is the contract signal; no exception for expected degradation; use case checks return value only | **Chosen** |

### Decision: extraction_vocabulary.py as module-level constants

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Inline constants in adapter class | Adapter file grows large; constants mixed with logic | Rejected |
| Shared constants module | Vocabulary is independently testable; adapter imports only what it needs | **Chosen** |

### Decision: display_authors as @property on DTO

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Utility function outside DTO | Caller must remember to call it; logic scattered | Rejected |
| `@property` on frozen dataclass | Zero cost; DTO is the natural owner of its display representation | **Chosen** |

### Decision: references=[] always (break ReferenceParser coupling)

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Call ReferenceParser inside adapter | Violates single-responsibility; `path` would be required for adapter | Rejected |
| references=[] unconditionally | Explicit boundary: references are a future slice; adapter contract is paragraphs-in, DTO-out | **Chosen** |

## Data Flow

```
caller
  │  paragraphs: list[str], path: str | None
  ▼
ExtractContentUseCase.execute()   [@generic_error_handler]
  │
  ├─1─► ContentExtractionPort.extract(paragraphs, path)
  │         ParagraphContentAdapter
  │           normalize paragraphs → DocumentEmpty if empty
  │           heuristics: title / authors / abstract / keywords / sections
  │           text counts: word_count, char_count, paragraph_count
  │           returns base DocumentContentDTO (references=[])
  │
  ├─2─► (path is not None) CharacterCountPort.count(path)
  │         Win32ComWordCountAdapter
  │           WIN32COM_AVAILABLE guard → return None if unavailable
  │           open Word via COM → CharacterCountDTO(word, char, para)
  │           on COM failure after retry → logger.warning(...); return None
  │
  ├─3─► counts is None → keep base DTO counts; counts is not None → merge
  │
  └─4─► build final DocumentContentDTO(
              **base_dto fields,
              word_count=accurate or text-based,
              char_count=accurate or text-based,
              paragraph_count=accurate or text-based
        )  ← single frozen constructor call
  │
  ▼
DocumentContentDTO (frozen)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/domain/document/content_extraction_port.py` | Create | `ContentExtractionPort` ABC with `extract(paragraphs, path=None)` |
| `src/domain/document/character_count_port.py` | Create | `CharacterCountPort` ABC with `count(path) -> CharacterCountDTO \| None` |
| `src/domain/dtos/character_count_dto.py` | Create | Frozen `CharacterCountDTO(word_count, char_count, paragraph_count)` |
| `src/domain/enums/extraction_fallback.py` | Create | `ExtractionFallback(str, Enum)` with `UNKNOWN_AUTHOR` |
| `src/domain/dtos/document_content_dto.py` | Modify | Add `display_authors` property using `ExtractionFallback.UNKNOWN_AUTHOR` |
| `src/infrastructure/adapters/document/extraction_vocabulary.py` | Create | `AUTHOR_BLACKLIST`, `SECTION_HEADERS`, `INSTITUTION_PATTERN`, `SECTION_PATTERNS` |
| `src/infrastructure/adapters/document/paragraph_content_adapter.py` | Create | `ParagraphContentAdapter(ContentExtractionPort)` with `@generic_error_handler` |
| `src/infrastructure/adapters/document/win32com_word_count_adapter.py` | Create | `Win32ComWordCountAdapter(CharacterCountPort)` with module-level `WIN32COM_AVAILABLE` |
| `src/application/extract_content_use_case.py` | Create | `ExtractContentUseCase` with `execute(paragraphs, path=None)` |
| `src/infrastructure/wirings/extract_content_use_case_wiring.py` | Create | `ExtractContentUseCaseWiring` with `create_use_case()` + `_get_*` private factories |
| `src/application/tests/test_extract_content_use_case.py` | Create | Unit tests for use case orchestration (mocked ports) |
| `src/domain/tests/document/test_paragraph_content_adapter.py` | Create | Unit tests for adapter heuristics |
| `src/infrastructure/tests/test_extract_content_use_case_wiring.py` | Create | Wiring smoke test (no I/O) |
| `tests/smoke/test_extract_content_parity.py` | Create | Parity test: legacy `ContentExtractor` vs new `ExtractContentUseCase` on sample docs |
| `data_access/content_extractor.py` | Unchanged | Legacy remains; coexists during migration |
| `data_access/word_counter.py` | Unchanged | Legacy remains; coexists during migration |

## Interfaces / Contracts

```python
# Ports
class ContentExtractionPort(ABC):
    @abstractmethod
    def extract(self, paragraphs: list[str], path: str | None = None) -> DocumentContentDTO: ...

class CharacterCountPort(ABC):
    @abstractmethod
    def count(self, path: str) -> CharacterCountDTO | None: ...

# DTOs
@dataclass(frozen=True)
class CharacterCountDTO(BaseDTO):
    word_count: int
    char_count: int
    paragraph_count: int

# DocumentContentDTO addition
@property
def display_authors(self) -> str:
    return self.authors or ExtractionFallback.UNKNOWN_AUTHOR

# Enum
class ExtractionFallback(str, Enum):
    UNKNOWN_AUTHOR = "Autor no identificado"

# Use case
class ExtractContentUseCase:
    def __init__(
        self,
        extraction_port: ContentExtractionPort,
        count_port: CharacterCountPort,
    ) -> None: ...

    @generic_error_handler
    def execute(
        self, paragraphs: list[str], path: str | None = None
    ) -> DocumentContentDTO: ...
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit — adapter | Normalize paragraphs; `DocumentEmpty` on empty input; title/authors/abstract/keywords/sections extraction; `_extract_sections()` called once (bug fix) | Pytest, string fixtures, no file I/O |
| Unit — use case | Count port called only when `path` given; `None` from count port → base counts kept; accurate counts merged correctly via `dataclasses.replace()`; `DocumentEmpty` propagates | Pytest with `MagicMock` ports |
| Unit — win32com adapter | `count()` returns `None` when `WIN32COM_AVAILABLE=False`; returns `None` and logs warning on COM failure | Monkeypatch `WIN32COM_AVAILABLE`; mock `win32com.client` |
| Unit — DTO property | `display_authors` returns value when set; returns `UNKNOWN_AUTHOR` when `None` | Simple dataclass construction |
| Integration — wiring | `create_use_case()` returns correctly wired instance; types match port contracts | Import + type check, no I/O |
| Smoke — parity | `ExtractContentUseCase.execute(paragraphs)` matches `ContentExtractor.extract_content(paragraphs)` for title, abstract, keywords, sections on ≥1 sample document | Load real `.docx`; compare fields; `path=None` (no COM needed) |

## Migration / Rollout

No migration required. Legacy `content_extractor.py` and `word_counter.py` are unchanged. `main.py` and `gradio_app.py` continue calling legacy classes. New wiring is self-contained under `src/` — no entry point wires it yet (next slice).

## Open Questions

- None. All decisions confirmed by proposal and architecture context.
