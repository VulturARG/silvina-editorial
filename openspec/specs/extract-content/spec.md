# Extract-Content Specification

## Purpose

Migrate `data_access/content_extractor.py` and `data_access/word_counter.py` into the hexagonal architecture. Expose `ExtractContentUseCase` that returns a frozen `DocumentContentDTO` from two clean ports: one for structural extraction, one for accurate character counting with graceful degradation.

---

## Requirements

### Requirement: ContentExtractionPort Contract

`ContentExtractionPort` MUST be an abstract base class at `src/domain/document/content_extraction_port.py` with exactly one abstract method: `extract(paragraphs: list[str], path: str | None = None) -> DocumentContentDTO`. It MUST NOT import any infrastructure or I/O symbols.

#### Scenario: Port interface is pure domain

- GIVEN `ContentExtractionPort` is imported from the domain layer
- WHEN its module is inspected for infrastructure imports
- THEN no infrastructure or file I/O symbols MUST be present
- AND the abstract method signature MUST match `extract(paragraphs, path=None) -> DocumentContentDTO`

---

### Requirement: CharacterCountPort Contract

`CharacterCountPort` MUST be an abstract base class at `src/domain/document/character_count_port.py` with exactly one abstract method: `count(path: str) -> CharacterCountDTO | None`. It MUST NOT import any infrastructure or win32com symbols.

#### Scenario: Port interface is pure domain

- GIVEN `CharacterCountPort` is imported from the domain layer
- WHEN its module is inspected
- THEN no win32com or infrastructure symbol MUST be present
- AND the abstract method signature MUST match `count(path: str) -> CharacterCountDTO | None`

---

### Requirement: CharacterCountDTO Value Object

`CharacterCountDTO` MUST be a frozen dataclass at `src/domain/dtos/character_count_dto.py` with fields `word_count: int`, `char_count: int`, `paragraph_count: int`.

#### Scenario: Immutability enforced

- GIVEN a `CharacterCountDTO` instance
- WHEN any field is reassigned
- THEN `FrozenInstanceError` MUST be raised

---

### Requirement: ExtractionFallback Enum

`ExtractionFallback` MUST be a `str`-based enum at `src/domain/enums/extraction_fallback.py` with member `UNKNOWN_AUTHOR = "Autor no identificado"`.

#### Scenario: Enum value is the display string

- GIVEN `ExtractionFallback.UNKNOWN_AUTHOR`
- WHEN coerced to `str`
- THEN the result MUST equal `"Autor no identificado"`

---

### Requirement: ParagraphContentAdapter — Structural Extraction

`ParagraphContentAdapter` MUST implement `ContentExtractionPort`. It MUST extract `title`, `authors` (None if not found), `abstract`, `keywords`, and `sections` from paragraphs using heuristics from `extraction_vocabulary.py`. In this adapter, `references` MUST always be `[]`; references are populated downstream by `DocumentContentExtractor` via `ReferenceExtractionPort`. `_extract_sections()` MUST be called exactly once per `extract()` invocation (fixes legacy double-call bug).

#### Scenario: Successful structural extraction

- GIVEN a non-empty paragraph list representing a valid document
- WHEN `extract(paragraphs)` is called
- THEN the returned `DocumentContentDTO` MUST contain non-empty `title`, `abstract`, `keywords`, and `sections`
- AND `references` MUST equal `[]`

#### Scenario: Empty paragraphs raise DocumentEmpty

- GIVEN a paragraph list that is empty or contains only blank strings after cleaning
- WHEN `extract(paragraphs)` is called
- THEN `DocumentEmpty` MUST be raised

#### Scenario: _extract_sections called exactly once

- GIVEN a valid paragraph list
- WHEN `extract(paragraphs)` is called
- THEN `_extract_sections()` MUST be invoked exactly once during that call

---

### Requirement: ParagraphContentAdapter — Text-Based Counts

When no accurate counts are available, `ParagraphContentAdapter` MUST compute `word_count`, `char_count`, and `paragraph_count` from the cleaned paragraph list and include them in the returned DTO.

#### Scenario: Counts derived from paragraphs

- GIVEN a paragraph list with a known total of words and characters
- WHEN `extract(paragraphs)` is called
- THEN `word_count`, `char_count`, and `paragraph_count` in the DTO MUST reflect that paragraph list

---

### Requirement: Win32ComWordCountAdapter

`Win32ComWordCountAdapter` MUST implement `CharacterCountPort`. When `WIN32COM_AVAILABLE` is `True` and Word succeeds, it MUST return a `CharacterCountDTO` with accurate counts. When COM fails after retry, it MUST log a warning and return `None`. When `WIN32COM_AVAILABLE` is `False`, it MUST return `None` immediately.

#### Scenario: Successful COM count

- GIVEN `WIN32COM_AVAILABLE` is `True` and a valid `.docx` path
- WHEN `count(path)` is called and Word opens the file without error
- THEN a `CharacterCountDTO` with `word_count > 0` MUST be returned

#### Scenario: COM failure returns None

- GIVEN `WIN32COM_AVAILABLE` is `True` but Word raises a COM error after retry
- WHEN `count(path)` is called
- THEN `None` MUST be returned and a warning MUST be logged

#### Scenario: win32com unavailable returns None

- GIVEN `WIN32COM_AVAILABLE` is `False`
- WHEN `count(path)` is called
- THEN `None` MUST be returned immediately

---

### Requirement: Content Extraction and Count Refinement Orchestration

> **Superseded (2026-07-04, `refactor_analyze_document_wiring`)**: `ExtractContentUseCase`
> and `ExtractContentUseCaseWiring` were eliminated as redundant pass-through layers.
> This orchestration now lives in `AnalyzeDocumentUseCase._extract_content()` — see
> `openspec/specs/analyze-document/spec.md`. `AnalyzeDocumentUseCaseWiring` builds
> `ContentExtractionPort` and `CharacterCountPort` directly via `_get_content_extraction_port()`
> and `_get_character_count_port()` (no intermediate sub-wiring).

`AnalyzeDocumentUseCase._extract_content(paragraphs, docx_path)` MUST call the extraction
port first. It MUST call the count port and merge the accurate counts when the port returns
a non-`None` result and does not raise `CharacterCountUnavailable`. If the count port raises
`CharacterCountUnavailable` or returns `None`, the base (text-based) `DocumentContentDTO`
from the extraction port MUST be kept unchanged.

#### Scenario: Accurate counts merged when the count port succeeds

- GIVEN a valid paragraph list, a `.docx` path, and `WIN32COM_AVAILABLE` is `True`
- WHEN `_extract_content(paragraphs, docx_path)` is called and COM succeeds
- THEN the returned DTO MUST carry the win32com-accurate counts

#### Scenario: Count port raises CharacterCountUnavailable — falls back to text-based counts

- GIVEN a valid paragraph list and a `.docx` path, but `count(docx_path)` raises
  `CharacterCountUnavailable`
- WHEN `_extract_content(paragraphs, docx_path)` is called
- THEN no exception MUST propagate to the caller
- AND the returned DTO MUST contain text-based counts

#### Scenario: Count port returns None — falls back to text-based counts

- GIVEN a valid paragraph list and a `.docx` path, but `count(docx_path)` returns `None`
- WHEN `_extract_content(paragraphs, docx_path)` is called
- THEN no exception MUST propagate to the caller
- AND the returned DTO MUST contain text-based counts

---

### Requirement: DocumentContentExtractor — Reference Population and Count Refinement

`DocumentContentExtractor` MUST reside in `src/domain/document/document_content_extractor.py`. It MUST receive `DocumentTextPort`, `ContentExtractionPort`, `CharacterCountPort`, and `ReferenceExtractionPort` via its constructor. In `extract_content(docx_path)`, it MUST read paragraphs via `DocumentTextPort`, obtain base content from `ContentExtractionPort`, extract references via `ReferenceExtractionPort.extract_references(docx_path=docx_path)`, and set `references` on the returned `DocumentContentDTO` via `dataclasses.replace`. This reference population MUST apply both when accurate counts are available and when character counting falls back (`CharacterCountPort` raises `CharacterCountUnavailable` or returns `None`). Errors raised by `ReferenceExtractionPort` MUST propagate without being swallowed.

#### Scenario: Accurate counts available and references populated

- GIVEN a valid `.docx` path
- AND `ReferenceExtractionPort` returns a non-empty list of references
- AND `CharacterCountPort` returns valid accurate counts
- WHEN `extract_content(docx_path)` is called
- THEN the returned `DocumentContentDTO` MUST contain the accurate counts
- AND its `references` MUST match the extracted references

#### Scenario: Character count unavailable falls back but populates references

- GIVEN a valid `.docx` path
- AND `ReferenceExtractionPort` returns a non-empty list of references
- AND `CharacterCountPort` raises `CharacterCountUnavailable`
- WHEN `extract_content(docx_path)` is called
- THEN no count exception MUST propagate
- AND the returned `DocumentContentDTO` MUST contain text-based counts
- AND its `references` MUST match the extracted references

#### Scenario: Character count returns None falls back but populates references

- GIVEN a valid `.docx` path
- AND `ReferenceExtractionPort` returns a non-empty list of references
- AND `CharacterCountPort` returns `None`
- WHEN `extract_content(docx_path)` is called
- THEN the returned `DocumentContentDTO` MUST contain text-based counts
- AND its `references` MUST match the extracted references

#### Scenario: Reference extraction error propagates

- GIVEN a valid `.docx` path
- AND `ReferenceExtractionPort` raises an exception
- WHEN `extract_content(docx_path)` is called
- THEN the exception MUST propagate to the caller

---

### Requirement: DocumentContentDTO display_authors Property

`DocumentContentDTO` MUST expose a `display_authors` computed property that returns `authors` when `authors` is not `None`, and `ExtractionFallback.UNKNOWN_AUTHOR` otherwise.

#### Scenario: Returns known authors

- GIVEN a `DocumentContentDTO` where `authors = "Jane Doe"`
- WHEN `display_authors` is accessed
- THEN `"Jane Doe"` MUST be returned

#### Scenario: Returns fallback when authors is None

- GIVEN a `DocumentContentDTO` where `authors = None`
- WHEN `display_authors` is accessed
- THEN `ExtractionFallback.UNKNOWN_AUTHOR` MUST be returned

---

### Requirement: Behavioral Parity with Legacy ContentExtractor

A smoke parity test MUST verify that `ContentExtractionPort.extract()` output matches legacy `ContentExtractor` output for `title`, `abstract`, `keywords`, and `sections` on real sample `.docx` files.

#### Scenario: Parity test passes on real samples

- GIVEN the same sample `.docx` file processed by both legacy `ContentExtractor` and
  `AnalyzeDocumentUseCaseWiring()._get_content_extraction_port().extract(paragraphs=...)`
- WHEN both produce their respective outputs
- THEN `title`, `abstract`, `keywords`, and `sections` MUST be equal between the two outputs
