# Feature: Include Tables in the Prompts, Follow-ups

- **Feature Name**: `include-tables-follow-ups`
- **File Locator**: `odd/tasks/include-tables-follow-ups.md`
- **Branch**: to be created from the branch that merges `feat/include-tables-in-prompt`; do not stack it on that branch before the pull request is decided.
- **Commit policy**: one work-unit commit per task, Conventional Commits, with its tests. `version.txt` must never be committed. Push and pull request wait for the user's order.
- **Status**: prepared, not started.

---

## 1. Origin

The native review of `include-tables-in-prompt` (lineage `review-9851f6d19af8deec`, 2026-10-17, lens `review-reliability`, base `92e1be2`) was approved with five advisory findings. None blocks and none reopens the review; the provider asks to treat them as separate work. The provider gave only the location of each finding, so the problem described below is a reading of the code in those lines and must be confirmed before changing anything.

## 2. Tasks

Ordered by the chance of hurting a real analysis.

- [ ] **TASK-01: A table that cannot be read must not stop the analysis (R3-001, WARNING).** `document_content_extractor.py:44-46` reads the tables inside the main flow, so an error while walking a malformed table would abort an analysis that worked before the feature. First reproduce it with a docx whose table breaks `DocxTableAdapter` (for example a table with a missing cell element). If it reproduces, decide between returning no tables for that document, or raising a domain error that the use case already maps; the preferred behavior is to analyze without tables, because the prompts worked without them. Acceptance: a test with the broken table that still returns the document content, and the unchanged behavior for a missing or corrupt file.
- [ ] **TASK-02: Bound the size of a table in the prompt (R3-002, WARNING).** `TableMarkdownRenderer.render` has no limit, and the length limit (`char_count`) does not see the tables, so a very large table grows the prompt with no guard. First measure the tables of the sample documents in `sandbox/` (rows, columns, characters of the Markdown) to see whether a limit is needed and where. If it is, the limit lives in `editorial_norms.toml` next to the other text limits, not in code, and a table above it is cut by rows with a visible note (for example `[tabla recortada: N filas más]`) instead of being dropped. Also decide whether the first row is always the header: the document does not mark it, so say so in the docstring or detect it. Acceptance: tests for the cut and for the note, and the measurement written in this file.
- [ ] **TASK-03: Merged cells without private attributes or quadratic cost (R3-003 and R3-004, WARNING).** `DocxTableAdapter._is_listed` compares `cell._tc` against every earlier cell, which uses a private python-docx attribute and costs O(cells²) per table. Keep a set of the identities already seen (for example the `id()` of the `_tc` element, or the element itself if it is hashable) per row and per table, so the lookup is constant. Check first whether python-docx 1.2.0 offers a public way to know that a cell is a continuation of a merge. Acceptance: the 12 existing adapter tests keep passing unchanged, plus a test with a table of 200 rows whose time stays bounded.
- [ ] **TASK-04: A table position outside the body must not vanish silently (R3-005, SUGGESTION).** `ArticleBodyDTO._blocks_in_document_order` ignores a table whose position is outside `0..len(paragraphs)`. The locator never produces one, so today it is only a guard. Decide between validating in `ArticleBodyDTO.__post_init__` (raise a domain error) and leaving it with a docstring that states the contract. Prefer the validation if it does not touch the 43 callers (the default is an empty tuple). Acceptance: a test with an out-of-range position.

## 3. Out of scope

- Images: the prompts carry only the figure captions and no image blocks (10 images in `02_IMRyD_Martinez_Garcia.docx`, none sent). It is a different feature and needs a model that accepts images.
- A real model run with tables: the next analysis will show the Markdown in `ai_interactions`; this is not a task, just something to look at.
- The ordering dependency between `read_paragraphs`, `DocxTableAdapter` and `ParagraphContentAdapter` (the three must count the same non-blank paragraphs) is not enforced by any test. A parity test over the sample documents would close it; add it to TASK-01 if the reproduction shows a mismatch.
