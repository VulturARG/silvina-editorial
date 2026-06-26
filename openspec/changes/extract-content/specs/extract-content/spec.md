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

`ParagraphContentAdapter` MUST implement `ContentExtractionPort`. It MUST extract `title`, `authors` (None if not found), `abstract`, `keywords`, and `sections` from paragraphs using heuristics from `extraction_vocabulary.py`. `references` MUST always be `[]`. `_extract_sections()` MUST be called exactly once per `extract()` invocation (fixes legacy double-call bug).

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

### Requirement: ExtractContentUseCase Orchestration

`ExtractContentUseCase.execute(paragraphs: list[str], path: str | None = None) -> DocumentContentDTO` MUST call the extraction port first. If `path` is provided, it MUST call the count port and merge the accurate counts when the port returns a non-`None` result. If the count port returns `None`, the use case MUST keep the text-based counts from the extraction port. The final `DocumentContentDTO` MUST be constructed in a single frozen constructor call.

#### Scenario: Execute without path returns text-based counts

- GIVEN a valid paragraph list and no `path`
- WHEN `execute(paragraphs)` is called
- THEN a `DocumentContentDTO` with text-based `word_count`, `char_count`, `paragraph_count` MUST be returned

#### Scenario: Execute with path returns accurate counts

- GIVEN a valid paragraph list, a `.docx` path, and `WIN32COM_AVAILABLE` is `True`
- WHEN `execute(paragraphs, path)` is called and COM succeeds
- THEN the returned DTO MUST carry the win32com-accurate counts

#### Scenario: Count port returns None — use case falls back to text-based counts

- GIVEN a valid paragraph list and a `.docx` path, but `count(path)` returns `None`
- WHEN `execute(paragraphs, path)` is called
- THEN no exception MUST propagate to the caller
- AND the returned DTO MUST contain text-based counts

---

### Requirement: ExtractContentUseCaseWiring

`ExtractContentUseCaseWiring` MUST follow the `ReadDocumentUseCaseWiring` instance-based factory pattern: a public `create_use_case()` method and private `_get_*()` helper methods for each dependency.

#### Scenario: Wiring produces a fully configured use case

- GIVEN `ExtractContentUseCaseWiring()` is instantiated
- WHEN `create_use_case()` is called
- THEN an `ExtractContentUseCase` with all ports injected MUST be returned

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

A smoke parity test MUST verify that `ExtractContentUseCase.execute()` output matches legacy `ContentExtractor` output for `title`, `abstract`, `keywords`, and `sections` on real sample `.docx` files.

#### Scenario: Parity test passes on real samples

- GIVEN the same sample `.docx` file processed by both legacy `ContentExtractor` and new `ExtractContentUseCase`
- WHEN both produce their respective outputs
- THEN `title`, `abstract`, `keywords`, and `sections` MUST be equal between the two outputs
