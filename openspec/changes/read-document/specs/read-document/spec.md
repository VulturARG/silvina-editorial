# Read Document Specification

## Purpose

Read raw paragraph text from a `.docx` file through a port/adapter pair
(`DocumentTextPort` / python-docx adapter), exposed via `ReadDocumentUseCase`.
First infrastructure-backed capability in the hexagonal migration; faithfully
replicates legacy `WordReader.read_word_document()` behavior without
constructing `DocumentContentDTO` (that assembly belongs to a later slice).

## Requirements

### Requirement: DocumentTextPort Contract

`DocumentTextPort` MUST be an abstract base class at
`src/domain/document/document_text_port.py` (entity-folder placement, not a
top-level `domain/ports/` folder) exposing exactly one abstract method:
`read_paragraphs(path: str) -> list[str]`. The port MUST NOT import
`python-docx` or any other infrastructure library.

#### Scenario: Port defines a single abstract method

- GIVEN `DocumentTextPort`
- WHEN its interface is inspected
- THEN it declares exactly one abstract method, `read_paragraphs(path: str) -> list[str]`

#### Scenario: Port has zero infrastructure imports

- GIVEN the file defining `DocumentTextPort`
- WHEN its import statements are inspected
- THEN none import `docx` or anything from `src/infrastructure/`

### Requirement: Adapter Reads Non-Empty Stripped Paragraphs

The python-docx adapter implementing `DocumentTextPort` MUST open the file at
`path`, iterate its paragraphs, strip each paragraph's text, and return only
the non-empty stripped strings, in document order — byte-for-byte parity with
legacy `WordReader.read_word_document()`.

#### Scenario: Whitespace-only paragraphs are excluded

- GIVEN a `.docx` file containing paragraphs `["Title", "   ", "Body text"]`
- WHEN `read_paragraphs(path)` is called
- THEN the result is `["Title", "Body text"]`

#### Scenario: Leading and trailing whitespace is stripped

- GIVEN a `.docx` file containing a paragraph `"  Indented text  "`
- WHEN `read_paragraphs(path)` is called
- THEN the corresponding entry in the result is `"Indented text"`

#### Scenario: Paragraph order is preserved

- GIVEN a `.docx` file with paragraphs in a specific order
- WHEN `read_paragraphs(path)` is called
- THEN the returned list preserves that same order

#### Scenario: Document with no non-empty paragraphs returns an empty list

- GIVEN a `.docx` file whose only paragraphs are empty or whitespace-only
- WHEN `read_paragraphs(path)` is called
- THEN the result is `[]`

### Requirement: Adapter Raises Typed Exceptions at the I/O Boundary

The adapter MUST raise `DocumentNotFound` (from
`src.domain.exceptions.document_errors`) when the file at `path` does not
exist, and `DocumentUnreadable` when `python-docx` fails to open or parse an
existing file. Neither failure MUST propagate as a bare built-in exception
(e.g. `FileNotFoundError`, `PackageNotFoundError`) to the caller.

#### Scenario: Missing file raises DocumentNotFound

- GIVEN a `path` that does not point to an existing file
- WHEN `read_paragraphs(path)` is called
- THEN `DocumentNotFound` is raised

#### Scenario: Corrupt or unparseable file raises DocumentUnreadable

- GIVEN a `path` pointing to an existing file that `python-docx` cannot parse
  (e.g. not a valid `.docx` package)
- WHEN `read_paragraphs(path)` is called
- THEN `DocumentUnreadable` is raised

#### Scenario: Valid file raises neither exception

- GIVEN a `path` pointing to a well-formed `.docx` file
- WHEN `read_paragraphs(path)` is called
- THEN no exception is raised and a `list[str]` is returned

### Requirement: ReadDocumentUseCase Thin Pass-Through

`ReadDocumentUseCase` (`src/application/read_document_use_case.py`) MUST
expose `execute(path: str) -> list[str]`, depending only on
`DocumentTextPort` and delegating to it without constructing
`DocumentContentDTO` or adding business logic. No domain service is
introduced for this slice.

#### Scenario: Use case returns the port's result unchanged

- GIVEN a `DocumentTextPort` test double returning `["A", "B"]` for a given path
- WHEN `ReadDocumentUseCase.execute(path)` is called with that path
- THEN the returned value is `["A", "B"]`

#### Scenario: Use case propagates port exceptions unchanged

- GIVEN a `DocumentTextPort` test double that raises `DocumentNotFound` for a
  given path
- WHEN `ReadDocumentUseCase.execute(path)` is called with that path
- THEN `DocumentNotFound` propagates out of `execute()` unmodified

#### Scenario: Use case does not construct DocumentContentDTO

- GIVEN the `ReadDocumentUseCase` source
- WHEN its imports and return type are inspected
- THEN it does not import or construct `DocumentContentDTO`

### Requirement: Wiring Follows the Instance-Based Factory Pattern

`ReadDocumentUseCaseWiring`
(`src/infrastructure/wirings/read_document_use_case_wiring.py`) MUST expose an
instance method `create_use_case() -> ReadDocumentUseCase`, constructing its
`DocumentTextPort` dependency via a private `_get_*()` method, matching the
pattern established by `validate_structure_wiring.py` and
`classify_article_use_case_wiring.py`.

#### Scenario: Wiring produces a usable use case instance

- GIVEN a `ReadDocumentUseCaseWiring` instance
- WHEN `create_use_case()` is called
- THEN it returns a `ReadDocumentUseCase` backed by a real adapter
  implementing `DocumentTextPort`, ready to call `.execute(path)`

#### Scenario: Wiring has no direct python-docx usage outside its adapter accessor

- GIVEN the `ReadDocumentUseCaseWiring` source
- WHEN its method bodies are inspected
- THEN `docx`-specific logic appears only inside the private `_get_*()`
  method that constructs the adapter, not inline in `create_use_case()`

### Requirement: Behavioral Parity with Legacy WordReader

For any sample `.docx` document readable by both implementations,
`ReadDocumentUseCase.execute(path)` MUST return a list equal to legacy
`WordReader.read_word_document(path)`'s return value.

#### Scenario: Parity smoke test passes against a real sample document

- GIVEN a real sample `.docx` file used elsewhere in the test suite
- WHEN both legacy `WordReader.read_word_document(path)` and
  `ReadDocumentUseCase.execute(path)` are called with that file
- THEN the two returned lists are equal element-for-element

## Out of Scope

- `win32com`-based counting (`data_access/word_counter.py`) — unrelated, Slice 6.
- Constructing `DocumentContentDTO` — Slice 6 (`ExtractContentUseCase`).
- Wiring `ReadDocumentUseCase` into `main.py` or `gradio_app.py` — Slice 14.
- `WordReader.read_document_with_styles()` and `get_document_properties()` —
  no current callers, not ported.
- Modifying or deleting `data_access/word_reader.py` — legacy stays untouched.
