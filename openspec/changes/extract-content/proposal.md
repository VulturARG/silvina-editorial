# Proposal: extract-content

## Intent

Migrate `data_access/content_extractor.py` (`ContentExtractor`) and `data_access/word_counter.py` (`WordCounter`) into the hexagonal architecture. Legacy classes couple content heuristics, character counting, and reference parsing in a single mutable return type (`DocumentContent`). This slice isolates content extraction and character counting behind clean ports, returning the existing frozen `DocumentContentDTO`, and fixes a double-call bug in `_extract_sections()`.

## Scope

### In Scope

- `ContentExtractionPort` + `ParagraphContentAdapter` (heuristics only, no file I/O)
- `CharacterCountPort` + `Win32ComWordCountAdapter` (win32com, graceful degradation)
- `ExtractContentUseCase` — calls both ports, merges counts, returns `DocumentContentDTO`
- `ExtractContentUseCaseWiring`
- `ExtractionFallback(str, Enum)` with `UNKNOWN_AUTHOR = "Autor no identificado"`
- `DocumentContentDTO.display_authors` property (returns `authors or ExtractionFallback.UNKNOWN_AUTHOR`)
- `CharacterCountDTO(word_count, char_count, paragraph_count)` — new frozen DTO
- `CountError(BaseSrcError)` base + `CharacterCountUnavailable(SrcBaseWarning)`
- `extraction_vocabulary.py` — vocabulary constants extracted from legacy `ContentExtractor`
- Bug fix: `_extract_sections()` called twice in legacy `extract_content()` — call once in adapter
- `references=[]` always (ReferenceParser coupling broken explicitly)
- Full test suite: adapter tests, use case tests, wiring test, smoke parity test

### Out of Scope

- win32com-based reference parsing (future slice)
- Wiring into `main.py` or `gradio_app.py` (later slice)
- `WordReader.read_document_with_styles()` and `get_document_properties()` (no callers)
- Deleting or modifying legacy `content_extractor.py` and `word_counter.py` (coexistence)

## Capabilities

### New Capabilities

- `content-extraction`: Port + adapter for structural extraction from paragraph list (title, authors, abstract, keywords, sections) with text-based fallback counts
- `character-count`: Port + adapter for accurate win32com-based word/char/paragraph counting with graceful degradation

### Modified Capabilities

- `document-content-dto`: Adds `display_authors` property — no requirement change, pure ergonomic addition

## Approach

Two-port design (plan §4.3, Approach B from exploration):

1. `ContentExtractionPort.extract(paragraphs, path=None) -> DocumentContentDTO` — adapter runs heuristics, computes text-based counts, returns DTO with `references=[]`
2. `CharacterCountPort.count(path) -> CharacterCountDTO | None` — adapter calls win32com; raises `CharacterCountUnavailable` on failure
3. `ExtractContentUseCase.execute(paragraphs, path=None)`:
   - Calls extraction port → base DTO
   - If `path` given: calls count port; on `CharacterCountUnavailable`, keeps text-based counts
   - Constructs final `DocumentContentDTO` in single frozen call

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/domain/document/` | New | `content_extraction_port.py`, `character_count_port.py` |
| `src/domain/dtos/` | New + Modified | `character_count_dto.py`; `document_content_dto.py` adds `display_authors` |
| `src/domain/enums/` | New | `extraction_fallback.py` |
| `src/domain/exceptions/` | New | `count_errors.py` |
| `src/infrastructure/adapters/document/` | New | `paragraph_content_adapter.py`, `win32com_word_count_adapter.py`, `extraction_vocabulary.py` |
| `src/application/` | New | `extract_content_use_case.py` |
| `src/infrastructure/wirings/` | New | `extract_content_use_case_wiring.py` |
| `tests/smoke/` | New | `test_extract_content_parity.py` |
| `data_access/content_extractor.py` | Unchanged | Legacy remains; coexists during migration |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Heuristic parity gap (adapter output differs from legacy) | Med | Smoke test compares legacy vs new on real sample documents |
| win32com unavailable in CI (Linux/macOS runners) | High | `WIN32COM_AVAILABLE` guard at module level; `CharacterCountUnavailable` caught in use case |
| Frozen DTO requires two-pass construction | Low | Extraction port returns base DTO; use case merges counts in single final constructor call |
| `_extract_sections()` bug fix introduces regression | Low | Unit tests cover section extraction before and after fix |

## Rollback Plan

No legacy files are modified. `main.py` and `gradio_app.py` continue to use legacy `ContentExtractor` directly. Remove new files under `src/` — zero impact on running system.

## Dependencies

- `DocumentEmpty` exception already present in `src/domain/exceptions/document_errors.py`
- `DocumentContentDTO` already exists in `src/domain/dtos/document_content_dto.py`
- `BaseSrcError` / `SrcBaseWarning` base classes already defined in domain exceptions
- win32com available only on Windows with Microsoft Word installed (test environment must mock)

## Success Criteria

- [ ] `ExtractContentUseCase.execute(paragraphs)` returns `DocumentContentDTO` without `path`
- [ ] `ExtractContentUseCase.execute(paragraphs, path)` returns DTO with win32com counts when available
- [ ] `CharacterCountUnavailable` caught; use case falls back to text-based counts without raising
- [ ] `ParagraphContentAdapter` raises `DocumentEmpty` on empty/all-blank paragraph list
- [ ] `DocumentContentDTO.display_authors` returns `"Autor no identificado"` when `authors=None`
- [ ] Smoke parity test passes: new output matches legacy for title, abstract, keywords, sections
- [ ] All new tests pass; no legacy tests broken
