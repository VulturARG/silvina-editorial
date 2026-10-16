# Feature: Analysis Report Defects

- **Feature Name**: `analysis-report-defects`
- **File Locator**: `odd/tasks/analysis-report-defects.md`
- **Branch**: `fix/analysis-report-defects`, from `silvina_editorial_v200`. It starts with the commits of the three earlier fixes (matcher by header, references by paragraph, feedback recommendation paragraph), cherry-picked, so that one pull request can carry the whole set. The three original branches stay untouched.
- **Commit policy**: commits by type in this order for each task: `docs`, then `fix`, then `test`; the fix commit includes the minimal adjustments to existing tests so the full suite passes; the test commit holds only new behavior tests that no existing test covers. The user does not want repeated tests and does not want tests that depend on the values of a configuration file. Commits are automatic at the end of each task; push and pull request wait for the user's order (the pull request is made at the end). `version.txt` has a local change of the user and must never be committed.

---

## 1. Origin

The verification (2026-10-15) of the two analyses (Claude Haiku 4.5 and gemma4) of `sandbox/pack_2/inputs/01_IMRyD_Cano_Martinez.docx` against the document and `data/metrics.db` found defects of the system, not of the models. The first two (citation and reference matching, recommendation paragraph) and the dimension matcher failure that stopped a run are already fixed on this branch.

## 2. Tasks

- [ ] **TASK-03: All the citations of a group.** `DocxCitationAdapter._collect_parenthetical` takes one citation per parenthesis, so `(Dupuy et al., 2021; Boyes, 2015)` loses everything after the first year. Split each parenthetical group on `;` and emit one `CitationDTO` per segment that has a year (text `(<segment>)`); keep the date-like skip and the deduplication by author and year. Expected effect on `01_IMRyD_Cano_Martinez.docx`: the four references reported as never cited (Ahmad, Boyes, Dash, Wolfowitz) are now cited.
- [ ] **TASK-04: Corporate author is not a conjunction error.** `ApaValidator` reports `McKinsey & Company` and suggests `McKinsey y Company`. A corporate author is recognized from the reference list, not from constants: the author part of a reference (text before the first `.` or ` (` that precedes the year) that contains ` & ` and is equal to the author part of the citation. People appear in the list with commas and initials (`Hines, A., & Bishop, P.`), so they never match. `validate_all_citations` receives the references; `AnalyzeDocumentUseCase._validate_apa` passes them; the conjunction check (parenthetical and narrative) is skipped for those authors.
- [ ] **TASK-05: Grammar offsets.** The offsets of the grammar errors are relative to the abstract plus the body joined with a newline (+834 in the sample), not to the body. Find who consumes `offset` and `length` (report, JSON); if nothing needs the offset, document the reference frame in `GrammarErrorDTO`, otherwise make it explicit.
- [ ] **TASK-06: Title and authors of the document info.** `document_info.authors` holds the affiliation and `title` concatenates the title and the author. Find the heuristic in `ParagraphContentAdapter` and fix it on the 30 sample documents without breaking the cases that work today.
- [ ] **TASK-07: Editorial suitability in the JSON.** The two suitability calls (contribution and alignment) cost 17 to 90 seconds but their result is missing from the JSON export (only the Word report shows it). Add it to the JSON export.
- [ ] **TASK-08: Investigate `pack_2/14` (de_Singlau).** 13 of 23 citations without a reference with 29 references: check whether it is a real mismatch or another extraction problem; fix only what is a defect.
