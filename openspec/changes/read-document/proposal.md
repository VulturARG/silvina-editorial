# Proposal: read-document (Slice 5)

## Intent

`data_access/word_reader.py` (`WordReader.read_word_document()`) is the only legacy
component that touches `python-docx` directly to read raw paragraph text from a `.docx`
file. It is the first I/O boundary in the migration plan and the prerequisite for every
later slice that needs document content (`ExtractContent`, citation/reference extraction).
Migrating it now establishes the first port/adapter pair (`DocumentTextPort`) and proves
the hexagonal pattern for a slice with real infrastructure, before slices with more complex
adapters build on it.

**Why now**: Slices 0–4 (DTOs, exceptions, pure domain services) are complete with no
infrastructure dependency. This is the next row in the plan (§8) and unblocks Slice 6
(`ExtractContent`).

**Success**: A new `ReadDocumentUseCase` returns the same `list[str]` of stripped,
non-empty paragraphs as legacy `read_word_document()` for the same input file, with
behavioral parity verified against real sample documents. No legacy file is modified.

## Scope

### In Scope

- `DocumentTextPort` at `src/domain/document/document_text_port.py` — one abstract method,
  `read_paragraphs(path: str) -> list[str]`, per the explicit decision to follow the
  clean-architecture SKILL's entity-folder rule (not the existing `domain/ports/` top-level
  precedent set by `LlmGeneratorPort`).
- An adapter implementing `DocumentTextPort` with `python-docx`, faithfully porting
  `WordReader.read_word_document()`: open the file, read paragraph text, strip whitespace,
  filter out empty paragraphs. Exact path/package name finalized in design.
- `ReadDocumentUseCase` in `src/application/` — thin pass-through:
  `execute(path: str) -> list[str]`. Returns the raw paragraph list; does NOT construct
  `DocumentContentDTO`.
- Production wiring in `src/infrastructure/wirings/`, following the existing instance-based
  `create_use_case()` / private `_get_*()` pattern.
- Explicit domain exceptions at the adapter boundary: raise `DocumentNotFound` when the
  file does not exist, `DocumentUnreadable` when `python-docx` fails to parse it — instead
  of relying solely on `@generic_error_handler`'s generic wrapping. Reuses existing
  exceptions from `src/domain/exceptions/document_errors.py` (Slice 1); no new exception
  types needed.
- Domain tests for the adapter (using real or minimal fixture `.docx` files) and the use
  case (with a fake `DocumentTextPort`).
- A parity smoke test comparing legacy `WordReader.read_word_document()` output against
  the new use case on a real sample document, following the existing
  `tests/smoke/test_validate_structure_parity.py` pattern.

### Out of Scope

- `win32com` — confirmed unrelated; used only by `data_access/word_counter.py` for
  character/word counts, a separate concern (Slice 6).
- Constructing `DocumentContentDTO` — that DTO assembly belongs to Slice 6
  (`ExtractContentUseCase`). This slice's use case returns `list[str]`, full stop.
- Wiring `ReadDocumentUseCase` into `main.py` or `gradio_app.py` — deferred to Slice 14
  (caller switchover). Both stacks coexist independently until then.
- `WordReader.read_document_with_styles()` and `get_document_properties()` — confirmed via
  grep to have no current callers in `main.py` or `content_extractor.py`. Not ported
  (YAGNI). No replacement port method added speculatively.
- Deleting or modifying `data_access/word_reader.py` — legacy stays untouched.
- Fixing the existing top-level `domain/ports/` precedent (`LlmGeneratorPort`) — tracked as
  separate tech debt, not addressed here.

## Capabilities

### New Capabilities

- `read-document`: capability to read raw paragraph text from a `.docx` file, exposed via
  `DocumentTextPort` / `ReadDocumentUseCase`. First infrastructure-backed capability in the
  migration.

### Modified Capabilities

- None.

## Approach

1. **Port** (`src/domain/document/document_text_port.py`) — single abstract method
   `read_paragraphs(path: str) -> list[str]`, matching the plan's §6 use-case contract
   exactly.
2. **Adapter** (`src/infrastructure/adapters/document/`, exact name in design) — wraps
   `docx.Document(path)`, iterates paragraphs, strips and filters empties (1:1 with legacy
   behavior). Catches missing-file and parse failures and raises `DocumentNotFound` /
   `DocumentUnreadable` explicitly, rather than letting the generic decorator mask the
   failure type.
3. **Use case** — depends only on `DocumentTextPort`; no domain service needed (this slice
   has no business logic beyond delegation, per the plan's §6 table: `ReadDocumentUseCase`
   row lists no domain service).
4. **Wiring** — same instance-based factory shape as `validate_structure_wiring.py` and
   `classify_article_use_case_wiring.py`.

## Affected Areas

| Area | Impact | Description |
|------|--------|--------------|
| `src/domain/document/document_text_port.py` | New | `DocumentTextPort` ABC |
| `src/infrastructure/adapters/document/` (name TBD in design) | New | python-docx adapter |
| `src/application/read_document_use_case.py` | New | `ReadDocumentUseCase` |
| `src/infrastructure/wirings/read_document_use_case_wiring.py` | New | Wiring factory |
| Domain/adapter/use-case tests (paths in design) | New | Behavioral + parity coverage |
| `data_access/word_reader.py` | Unchanged | Legacy stays alive during coexistence |
| `main.py` / `gradio_app.py` | Unchanged | Not wired in this slice (Slice 14) |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Paragraph-filtering edge cases (whitespace-only, special chars) diverge from legacy | Low | Parity smoke test against real sample documents |
| Exception type at adapter boundary misclassifies a failure (e.g. corrupt file treated as not-found) | Low | Explicit tests for both `DocumentNotFound` and `DocumentUnreadable` paths |
| Two parallel document-reading paths (legacy + new) coexist unconnected until Slice 14 | Low (accepted) | Explicitly out of scope; no shared state, zero coupling risk |

## Rollback Plan

All new files are additive (new port, adapter, use case, wiring, tests). Legacy
`data_access/word_reader.py` is untouched and nothing currently calls the new code. To roll
back: delete the new port, adapter, use case, wiring, and test files. No migration state to
undo.

## Dependencies

- Slice 1 exceptions: `DocumentNotFound`, `DocumentUnreadable` from
  `src/domain/exceptions/document_errors.py` — already exist, reused as-is.
- `python-docx` — already a project dependency (used by legacy `WordReader`).

## Success Criteria

- [ ] `ReadDocumentUseCase.execute(path)` returns the same paragraph list as legacy
      `WordReader.read_word_document()` for identical sample documents
- [ ] `DocumentTextPort` lives at `src/domain/document/document_text_port.py` (entity
      folder, not a top-level `ports/` folder)
- [ ] Adapter raises `DocumentNotFound` for missing files and `DocumentUnreadable` for
      unparseable files, not bare built-in exceptions
- [ ] `win32com`, `DocumentContentDTO` construction, and `main.py`/`gradio_app.py` wiring
      are not touched by this slice
- [ ] `data_access/word_reader.py` is unmodified
- [ ] All new domain/application/adapter tests pass under strict TDD
      (`python -m pytest src/ -q`)

## Proposal question round

This is a pure architecture migration (fixed legacy behavioral contract, no new product
surface), so standard business-question categories mostly don't apply. Three scope/risk
assumptions were surfaced to the user for confirmation before finalizing:

1. Exclude `read_document_with_styles()` / `get_document_properties()` entirely (no
   callers found) — assumed agreed.
2. Adapter raises typed domain exceptions (`DocumentNotFound`/`DocumentUnreadable`)
   explicitly at the boundary rather than relying only on the generic error-handler
   wrapper — assumed agreed.
3. Legacy `WordReader` and the new `ReadDocumentUseCase` remain unconnected until Slice 14
   — assumed agreed (consistent with all prior slices' coexistence pattern).

These assumptions are reflected in the Scope/Approach sections above. Flag here if any
should change before moving to spec/design.
