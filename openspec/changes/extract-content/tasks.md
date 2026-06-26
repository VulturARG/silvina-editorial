# Tasks: extract-content

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 580–650 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 → PR 2 → PR 3 |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: pending
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Domain ports, DTOs, enum, test doubles, DTO modification | PR 1 | Base: feat/slice7-read-document; ~150 lines |
| 2 | extraction_vocabulary + adapters + adapter tests | PR 2 | Base: PR 1 branch; ~260 lines |
| 3 | Use case + wiring + smoke test | PR 3 | Base: PR 2 branch; ~180 lines |

## Phase 1: Domain Foundation

- [ ] 1.1 RED — Create `src/domain/tests/document/test_content_extraction_port.py`: assert `ContentExtractionPort` is ABC; `extract(paragraphs, path=None) -> DocumentContentDTO` signature; no infrastructure imports.
- [ ] 1.2 GREEN — Create `src/domain/document/content_extraction_port.py`: `ContentExtractionPort(ABC)`, single abstract `extract()`.
- [ ] 1.3 RED — Create `src/domain/tests/document/test_character_count_port.py`: assert `CharacterCountPort` is ABC; `count(path) -> CharacterCountDTO | None` signature; no win32com imports; `CharacterCountDTO` raises `FrozenInstanceError` on reassignment.
- [ ] 1.4 GREEN — Create `src/domain/document/character_count_port.py`: `CharacterCountPort(ABC)`, single abstract `count()`.
- [ ] 1.5 GREEN — Create `src/domain/dtos/character_count_dto.py`: `@dataclass(frozen=True)` with `word_count`, `char_count`, `paragraph_count` (satisfies 1.3 immutability scenario).
- [ ] 1.6 GREEN — Create `src/domain/enums/extraction_fallback.py`: `ExtractionFallback(str, Enum)` with `UNKNOWN_AUTHOR = "Autor no identificado"`.
- [ ] 1.7 RED — Add `display_authors` scenarios to `test_content_extraction_port.py`: returns `authors` when not `None`; returns `ExtractionFallback.UNKNOWN_AUTHOR` when `None`.
- [ ] 1.8 GREEN — Modify `src/domain/dtos/document_content_dto.py`: add `from src.domain.enums.extraction_fallback import ExtractionFallback`; add `@property display_authors(self) -> str`.
- [ ] 1.9 Create `src/domain/tests/document/fake_content_extraction_port.py`: `FakeContentExtractionPort(ContentExtractionPort)`, configurable DTO return or error.
- [ ] 1.10 Create `src/domain/tests/document/fake_character_count_port.py`: `FakeCharacterCountPort(CharacterCountPort)`, configurable `CharacterCountDTO | None` return.

## Phase 2: Vocabulary Constants

- [ ] 2.1 Create `src/infrastructure/adapters/document/extraction_vocabulary.py`: extract `AUTHOR_BLACKLIST`, `SECTION_HEADERS`, `INSTITUTION_PATTERN`, `SECTION_PATTERNS` from `data_access/content_extractor.py` as module-level constants.

## Phase 3: Infrastructure Adapters

- [ ] 3.1 RED — Create `src/infrastructure/tests/adapters/document/test_paragraph_content_adapter.py`: empty paragraphs → `DocumentEmpty`; valid input → non-empty title/abstract/keywords/sections; `references == []`; `_extract_sections()` called exactly once; text-based counts populated.
- [ ] 3.2 GREEN — Create `src/infrastructure/adapters/document/paragraph_content_adapter.py`: `ParagraphContentAdapter(ContentExtractionPort)` importing from `extraction_vocabulary.py`; single `_extract_sections()` call; `references=[]`; text-based counts from cleaned paragraphs.
- [ ] 3.3 RED — Create `src/infrastructure/tests/adapters/document/test_win32com_word_count_adapter.py`: monkeypatch `WIN32COM_AVAILABLE=False` → `count()` returns `None`; mock COM exception → `count()` returns `None` and `logger.warning()` fired.
- [ ] 3.4 GREEN — Create `src/infrastructure/adapters/document/win32com_word_count_adapter.py`: `Win32ComWordCountAdapter(CharacterCountPort)`; module-level `WIN32COM_AVAILABLE`; returns `None` immediately when unavailable; logs `logger.warning()` and returns `None` on COM failure after retry; returns `CharacterCountDTO` on success.

## Phase 4: Application Layer

- [ ] 4.1 RED — Create `src/application/tests/test_extract_content_use_case.py`: no `path` → count port not called, text-based counts returned; with `path` and non-`None` counts → `dataclasses.replace()` merges accurate counts; count port returns `None` → base counts kept unchanged; `DocumentEmpty` from extraction port propagates.
- [ ] 4.2 GREEN — Create `src/application/extract_content_use_case.py`: `@generic_error_handler execute(paragraphs, path=None)`; calls extraction port first; if `path is not None`, calls count port; applies `dataclasses.replace(base_dto, word_count=..., char_count=..., paragraph_count=...)` only when counts is not `None`.

## Phase 5: Wiring

- [ ] 5.1 RED — Create `src/infrastructure/tests/test_extract_content_use_case_wiring.py`: `ExtractContentUseCaseWiring().create_use_case()` returns `ExtractContentUseCase` instance.
- [ ] 5.2 GREEN — Create `src/infrastructure/wirings/extract_content_use_case_wiring.py`: `create_use_case()` wires `ParagraphContentAdapter` and `Win32ComWordCountAdapter`; `_get_extraction_port()` and `_get_count_port()` private helpers following `ReadDocumentUseCaseWiring` pattern.

## Phase 6: Smoke Test

- [ ] 6.1 Create `tests/smoke/test_extract_content_parity.py`: `TestCase` with `setUpClass`; compare `ExtractContentUseCase.execute(paragraphs, path=None)` vs legacy `ContentExtractor` for `title`, `abstract`, `keywords`, `sections` on ≥1 sample `.docx`; no `sys.path.insert`; reuse `DOCS` path pattern from `test_read_document_parity.py`.
