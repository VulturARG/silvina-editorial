# Delta Spec: Domain Exceptions (Slice 1)

> Normative guide: `.agent/skills/clean-architecture/SKILL.md`
> Parent proposal: `openspec/changes/domain-exceptions/proposal.md`
> Migration plan reference: `docs/plan-migracion-hexagonal.md` §7

---

## Purpose

This spec defines WHAT must be true after the domain-exceptions slice is
applied. Every requirement is expressed as a testable assertion; each scenario
translates directly to a `unittest.TestCase`.

---

## Exception Groups (resolved — matches plan §7)

Five domain groupings need typed exceptions. Each group file lives in
`src/domain/exceptions/` and holds one or more exception classes.

| File | Classes | Base(s) |
|---|---|---|
| `document_errors.py` | `DocumentNotFound`, `DocumentEmpty`, `DocumentUnreadable` | `SrcBaseNotFound`, `SrcBaseWarning` |
| `citation_errors.py` | `CitationParsingFailed` | `SrcBaseWarning` |
| `classification_errors.py` | `ClassificationFailed` | `SrcBaseWarning` |
| `quality_errors.py` | `QualityAnalysisFailed` | `SrcBaseWarning` |
| `language_model_errors.py` | `LanguageModelUnavailable`, `LanguageModelNotFound`, `LanguageModelLoadFailed` | `LanguageModelError`, `BaseSrcError` |

---

## Requirement: Document Errors

### REQ-EXC-DOC-1 — DocumentNotFound inherits SrcBaseNotFound

`DocumentNotFound` SHALL be defined in `src/domain/exceptions/document_errors.py`
and MUST be a subclass of `SrcBaseNotFound`.

#### Scenario: DocumentNotFound is a SrcBaseNotFound

- GIVEN `from src.domain.exceptions.document_errors import DocumentNotFound`
- WHEN `issubclass(DocumentNotFound, SrcBaseNotFound)` is checked
- THEN the result is `True`

#### Scenario: DocumentNotFound is catchable as BaseSrcError

- GIVEN a `DocumentNotFound` instance is raised
- WHEN caught with `except BaseSrcError`
- THEN it is caught successfully

### REQ-EXC-DOC-2 — DocumentEmpty inherits SrcBaseWarning

`DocumentEmpty` SHALL be defined in `src/domain/exceptions/document_errors.py`
and MUST be a subclass of `SrcBaseWarning`.

#### Scenario: DocumentEmpty is a SrcBaseWarning

- GIVEN `from src.domain.exceptions.document_errors import DocumentEmpty`
- WHEN `issubclass(DocumentEmpty, SrcBaseWarning)` is checked
- THEN the result is `True`

#### Scenario: DocumentEmpty is catchable as BaseSrcError

- GIVEN a `DocumentEmpty` instance is raised
- WHEN caught with `except BaseSrcError`
- THEN it is caught successfully

### REQ-EXC-DOC-3 — DocumentUnreadable inherits SrcBaseWarning

`DocumentUnreadable` SHALL be defined in `src/domain/exceptions/document_errors.py`
and MUST be a subclass of `SrcBaseWarning`.

#### Scenario: DocumentUnreadable is a SrcBaseWarning

- GIVEN `from src.domain.exceptions.document_errors import DocumentUnreadable`
- WHEN `issubclass(DocumentUnreadable, SrcBaseWarning)` is checked
- THEN the result is `True`

#### Scenario: DocumentUnreadable is catchable as BaseSrcError

- GIVEN a `DocumentUnreadable` instance is raised
- WHEN caught with `except BaseSrcError`
- THEN it is caught successfully

---

## Requirement: Citation Errors

### REQ-EXC-CIT-1 — CitationParsingFailed inherits SrcBaseWarning

`CitationParsingFailed` SHALL be defined in
`src/domain/exceptions/citation_errors.py` and MUST be a subclass of
`SrcBaseWarning`.

#### Scenario: CitationParsingFailed is a SrcBaseWarning

- GIVEN `from src.domain.exceptions.citation_errors import CitationParsingFailed`
- WHEN `issubclass(CitationParsingFailed, SrcBaseWarning)` is checked
- THEN the result is `True`

#### Scenario: CitationParsingFailed is catchable as BaseSrcError

- GIVEN a `CitationParsingFailed` instance is raised
- WHEN caught with `except BaseSrcError`
- THEN it is caught successfully

---

## Requirement: Classification Errors

### REQ-EXC-CLASS-1 — ClassificationFailed inherits SrcBaseWarning

`ClassificationFailed` SHALL be defined in
`src/domain/exceptions/classification_errors.py` and MUST be a subclass of
`SrcBaseWarning`.

#### Scenario: ClassificationFailed is a SrcBaseWarning

- GIVEN `from src.domain.exceptions.classification_errors import ClassificationFailed`
- WHEN `issubclass(ClassificationFailed, SrcBaseWarning)` is checked
- THEN the result is `True`

#### Scenario: ClassificationFailed is catchable as BaseSrcError

- GIVEN a `ClassificationFailed` instance is raised
- WHEN caught with `except BaseSrcError`
- THEN it is caught successfully

---

## Requirement: Quality Errors

### REQ-EXC-QUAL-1 — QualityAnalysisFailed inherits SrcBaseWarning

`QualityAnalysisFailed` SHALL be defined in
`src/domain/exceptions/quality_errors.py` and MUST be a subclass of
`SrcBaseWarning`.

#### Scenario: QualityAnalysisFailed is a SrcBaseWarning

- GIVEN `from src.domain.exceptions.quality_errors import QualityAnalysisFailed`
- WHEN `issubclass(QualityAnalysisFailed, SrcBaseWarning)` is checked
- THEN the result is `True`

#### Scenario: QualityAnalysisFailed is catchable as BaseSrcError

- GIVEN a `QualityAnalysisFailed` instance is raised
- WHEN caught with `except BaseSrcError`
- THEN it is caught successfully

---

## Requirement: Language Model Errors

### REQ-EXC-LM-1 — LanguageModelUnavailable inherits SrcBaseWarning

`LanguageModelUnavailable` SHALL be defined in
`src/domain/exceptions/language_model_errors.py` and MUST be a subclass of
`SrcBaseWarning`.

#### Scenario: LanguageModelUnavailable is a SrcBaseWarning

- GIVEN `from src.domain.exceptions.language_model_errors import LanguageModelUnavailable`
- WHEN `issubclass(LanguageModelUnavailable, SrcBaseWarning)` is checked
- THEN the result is `True`

#### Scenario: LanguageModelUnavailable is catchable as BaseSrcError

- GIVEN a `LanguageModelUnavailable` instance is raised
- WHEN caught with `except BaseSrcError`
- THEN it is caught successfully

### REQ-EXC-LM-2 — LanguageModelNotFound inherits LanguageModelError

`LanguageModelNotFound` SHALL be defined in
`src/domain/exceptions/language_model_errors.py` and MUST be a subclass of
`LanguageModelError`.

#### Scenario: LanguageModelNotFound is a LanguageModelError

- GIVEN `from src.domain.exceptions.language_model_errors import LanguageModelNotFound, LanguageModelError`
- WHEN `issubclass(LanguageModelNotFound, LanguageModelError)` is checked
- THEN the result is `True`

#### Scenario: LanguageModelNotFound is catchable as BaseSrcError

- GIVEN a `LanguageModelNotFound` instance is raised
- WHEN caught with `except BaseSrcError`
- THEN it is caught successfully

#### Scenario: LanguageModelNotFound defines its own MESSAGE

- GIVEN `LanguageModelNotFound`
- WHEN `LanguageModelNotFound.MESSAGE` is inspected
- THEN it equals `"The configured language model is not installed in the backend."`

### REQ-EXC-LM-3 — LanguageModelLoadFailed inherits LanguageModelError

`LanguageModelLoadFailed` SHALL be defined in
`src/domain/exceptions/language_model_errors.py` and MUST be a subclass of
`LanguageModelError`.

#### Scenario: LanguageModelLoadFailed is a LanguageModelError

- GIVEN `from src.domain.exceptions.language_model_errors import LanguageModelLoadFailed, LanguageModelError`
- WHEN `issubclass(LanguageModelLoadFailed, LanguageModelError)` is checked
- THEN the result is `True`

#### Scenario: LanguageModelLoadFailed is catchable as BaseSrcError

- GIVEN a `LanguageModelLoadFailed` instance is raised
- WHEN caught with `except BaseSrcError`
- THEN it is caught successfully

#### Scenario: LanguageModelLoadFailed defines its own MESSAGE

- GIVEN `LanguageModelLoadFailed`
- WHEN `LanguageModelLoadFailed.MESSAGE` is inspected
- THEN it equals `"The language model could not be loaded or run by the backend. Check the available memory and the backend log."`

---

## Requirement: Ollama Generator Adapter Error Mapping

### REQ-EXC-LM-ADAPTER-1 — Map backend exceptions to specific LanguageModelError subclasses

`OllamaGeneratorAdapter.generate` SHALL map backend exceptions to specific subclasses of `LanguageModelError`, preserving the original exception as `__cause__`:
- `ollama.ResponseError` with `status_code == HTTPStatus.NOT_FOUND` maps to `LanguageModelNotFound`.
- `ollama.ResponseError` with `status_code >= HTTPStatus.INTERNAL_SERVER_ERROR` maps to `LanguageModelLoadFailed`.
- Any other `ollama.ResponseError`, `ollama.RequestError`, or `ConnectionError` maps to `LanguageModelUnavailable`.

#### Scenario: 404 ResponseError maps to LanguageModelNotFound with cause

- GIVEN an `OllamaGeneratorAdapter` instance
- WHEN `generate` encounters `ollama.ResponseError` with `status_code == 404`
- THEN `LanguageModelNotFound` is raised
- AND `__cause__` is the original `ResponseError`

#### Scenario: 500+ ResponseError maps to LanguageModelLoadFailed with cause

- GIVEN an `OllamaGeneratorAdapter` instance
- WHEN `generate` encounters `ollama.ResponseError` with `status_code >= 500` (e.g. 500, 503)
- THEN `LanguageModelLoadFailed` is raised
- AND `__cause__` is the original `ResponseError`

#### Scenario: Other backend errors map to LanguageModelUnavailable with cause

- GIVEN an `OllamaGeneratorAdapter` instance
- WHEN `generate` encounters any other `ollama.ResponseError` (e.g. 400), `ollama.RequestError`, or `ConnectionError`
- THEN `LanguageModelUnavailable` is raised
- AND `__cause__` is the original backend exception

---

## Requirement: MESSAGE Attribute

### REQ-EXC-MSG-1 — Every exception class defines a MESSAGE attribute

Each exception class in this slice MUST define a `MESSAGE: str` class attribute.
`BaseSrcError.dict()` reads `self.MESSAGE`; a missing or `None` `MESSAGE` falls
back to a default string naming the class, which leaks implementation names to
entry points.

#### Scenario: Each exception has a non-None MESSAGE

- GIVEN any exception class defined in this slice
- WHEN `ExceptionClass.MESSAGE` is inspected
- THEN it is a non-empty string (not `None`)

---

## Requirement: Import Conventions

### REQ-EXC-IMPORTS-1 — Group files import only from base_src_error

Each `<group>_errors.py` file MUST import only from
`src.domain.exceptions.base_src_error`. No other imports.

#### Scenario: document_errors.py imports only base types

- GIVEN `src/domain/exceptions/document_errors.py`
- WHEN the module-level import statements are inspected
- THEN only `SrcBaseNotFound` and `SrcBaseWarning` are imported, from
  `src.domain.exceptions.base_src_error`; no other import is present

### REQ-EXC-IMPORTS-2 — No local imports, no wildcard imports

SKILL §3: no imports inside functions or methods; no `import *`.

#### Scenario: No in-function imports in any group file

- GIVEN all five `<group>_errors.py` files
- WHEN each file's import statements are scanned
- THEN all imports are at module top level; no indented `import` or
  `from ... import` statements appear inside class bodies or methods

---

## Requirement: Test Coverage

### REQ-EXC-TEST-1 — Each group has a unittest.TestCase file

Every exception group file MUST have a corresponding test file under
`src/domain/tests/exceptions/`.

| Group file | Test file |
|---|---|
| `document_errors.py` | `src/domain/tests/exceptions/test_document_errors.py` |
| `citation_errors.py` | `src/domain/tests/exceptions/test_citation_errors.py` |
| `classification_errors.py` | `src/domain/tests/exceptions/test_classification_errors.py` |
| `quality_errors.py` | `src/domain/tests/exceptions/test_quality_errors.py` |
| `language_model_errors.py` | `src/domain/tests/exceptions/test_language_model_errors.py` |

#### Scenario: Test suite passes after all groups are implemented

- GIVEN all 5 group files and their test files exist
- WHEN `python -m pytest src/` is executed
- THEN all tests pass with zero failures or errors

### REQ-EXC-TEST-2 — Tests use unittest.TestCase exclusively

#### Scenario: Test files use TestCase

- GIVEN any test file in `src/domain/tests/exceptions/` created by this slice
- WHEN the file is inspected for the base class
- THEN the test class extends `unittest.TestCase` imported as
  `from unittest import TestCase`

---

## Requirement: Coexistence

### REQ-EXC-COEX-1 — Legacy code remains unmodified

No file outside `src/domain/exceptions/` and `src/domain/tests/exceptions/`
is modified. The new exception classes are defined but not yet raised by any
production caller.

#### Scenario: Legacy pytest suite still passes

- GIVEN the slice is applied
- WHEN `python -m pytest tests/` is executed
- THEN all legacy tests pass (no regressions)

---

## Out of Scope

- Raising these exceptions in any use case, adapter, or service (each later slice).
- Adding new exception groups beyond the 5 in plan §7.
- Modifying `base_src_error.py` or `generic_error_handler.py`.
- Ports, adapters, wirings, use cases.
