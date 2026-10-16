# Feature: Reference Extraction By Paragraph

- **Feature Name**: `reference-extraction-by-paragraph`
- **File Locator**: `odd/tasks/reference-extraction-by-paragraph.md`
- **Branch**: `fix/reference-extraction-by-paragraph`, from `silvina_editorial_v200`
- **Commit policy**: commits by type in this order: `docs`, then `fix`, then `test`; the fix commit includes the minimal adjustments to existing tests so that the full suite passes; the test commit holds only new behavior tests that no existing test covers, preferably in the existing test file. The user does not want repeated tests. Push and pull request are the user's decision. `version.txt` has a local change of the user and must not be committed.

---

## 1. Problem

The verification of the analysis of `sandbox/pack_2/inputs/01_IMRyD_Cano_Martinez.docx` (2026-10-15) found that the report says 50 citations, 38 references and 25 citations without a reference (50.0 percent), while the document has 54 references and only one real mismatch (Lastra 2007). The 50.0 percent exactly equals the critical threshold, so the verdict and the only recommendation of the report come from false data.

Causes in `DocxReferenceAdapter`:

- The paragraphs are joined with `"".join`, so the end of an entry and the author of the next one are glued together.
- `_YEAR_END_PATTERN` does not recognize `(2021, 9 de mayo)`.
- Entries are cut by year tokens and the leftover title text is cleaned with a regex that sometimes starts inside a title. Wrong keys result (`cyber`, `en`, `nulty`) and 16 of the 54 references are lost.

## 2. Evidence that the cause is only the reference parsing

A one-off experiment (not committed) parsed the references of that document one per paragraph, cut at the first year token, and ran the unchanged `CitationMatcher`: 50 citations, 54 references, 1 unmatched citation (Lastra 2007, a real mismatch). The 4 references reported as never cited (Ahmad, Boyes, Dash, Wolfowitz) are the citations lost by a different known defect (only the first citation of a group separated by `;` is extracted), out of scope here. `CitationMatcher` needs no change.

## 3. Design

- `DocxReferenceAdapter` receives `BibliographyNormsDTO` (the same `header_markers` and `header_max_length` of `editorial_norms.toml` that `ArticleBodyLocator` uses; no marker constants in the code).
- The bibliography header is the last paragraph whose stripped lowercase text has at most `header_max_length` characters and contains one of the markers. Without a header: no references and the default section type, as before.
- Each non-empty paragraph after the header is one reference. The `ReferenceDTO.text` keeps the previous shape (author part up to and including the first year token, so recency and matching keep working) but the year token accepts `(2021)`, `(2021a)`, `(15 de enero de 2021)` and `(2021, 9 de mayo)`; a paragraph without year token keeps its whole cleaned text.
- Section type is resolved from the header paragraph as before (`ibliograf` -> Bibliografía, `fuentes` -> Fuentes bibliográficas, otherwise Referencias).
- `_BIB_SECTION_PATTERN`, `_AUTHOR_CLEANUP_PATTERN` and the split-by-year logic are removed. `AnalyzeDocumentUseCaseWiring` passes the norms.

## 4. Tasks

- [ ] **TASK-01: Parse references one per paragraph**: adapter, wiring, minimal adjustment of the existing tests (including `tests/smoke/test_extract_content_references_parity.py` if it pins the old output), and one new test only for what no existing test covers.
  - Done when: the full suite passes in every commit, `ruff` is clean, and the experiment above gives 50 citations, 54 references and 1 unmatched citation on the real document when run through the real adapter.
