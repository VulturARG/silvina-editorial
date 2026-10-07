# Feature: DocxReportAdapter SOLID refactor

- **Feature Name**: `docx-report-adapter-solid`
- **File Locator**: `odd/tasks/docx-report-adapter-solid.md`
- **Branch**: `refactor/docx-report-adapter-solid` (from `silvina_editorial_v100`)
- **TDD Mode**: Characterization first, then behavior-preserving refactor (every commit green)
- **TDD Runner**: `python -m pytest src/ tests/`; lint `python -m ruff check src/`
- **Delivery Strategy**: one work-unit commit per task on the feature branch; push/PR are the user's decision

---

## 1. Objective

`src/infrastructure/adapters/report/docx_report_adapter.py` (630 lines) is one class that orchestrates the export, builds 12 report sections, writes Word page furniture (header logo, page numbers, base style), parses Markdown and normalizes feedback blocks. It violates SRP and OCP and breaks several `AGENTS.md` / clean-architecture SKILL rules. Refactor it into small single-purpose collaborators while keeping the exported `.docx` byte-for-byte equivalent in content and formatting.

## 2. Findings that drive the plan

- SRP: sections, page decorations, Markdown parsing, feedback-block normalization and score-to-color mapping all live in one class.
- OCP: adding a section means editing `export()` and the class.
- DIP: `datetime.now()` is called inside the adapter (header and footer); the section list is hardcoded.
- Duplication: the colored section heading block (11 times), the `"Label: " bold + value` paragraph pair (about 25 times), `_format_match_rate` used by two sections.
- AGENTS.md / SKILL violations: inline comment `# Logo is decorative...`; abbreviations (`doc`, `err`, `rec`, `dim_name`, `dim_data`); `Any` and untyped `doc`; dicts rebuilt on every call (`verdict_colors`, `priority_icons`); magic numbers (indent inches, `"─" * 80`, border names); duck typing `dict | object` for feedback blocks.
- Tests call private methods (`adapter._add_*`) and patch `docx_report_adapter.Document` / `DOCX_AVAILABLE`.

## 3. Target design (all under `src/infrastructure/adapters/report/`, one class per file, flat like the existing helpers)

- `DocxReportSection` (ABC, `render(document, report_input) -> None`) and `DocxPageDecoration` (ABC, `apply(document) -> None`).
- Writers: `DocxMarkdownRunWriter`, `DocxFeedbackBlockWriter`, `DocxSectionHeadingWriter`, `DocxLabeledParagraphWriter`, `CitationMatchRateFormatter`.
- Sections (one file each): title page, executive summary, document info, classification, quality analysis, editorial suitability, grammar analysis, APA validation, structure validation, citations analysis, recommendations, footer.
- Decorations: `DocxBaseStyleDecoration`, `DocxHeaderLogoDecoration`, `DocxPageNumberDecoration`.
- `DocxReportAdapter` becomes a thin orchestrator: receives `page_decorations` and `sections` (ordered), creates `Document()`, applies decorations, renders sections, saves. It keeps `DOCX_AVAILABLE`, `Document` and the `ReportExportUnavailable` guard in its own module so existing patches keep working.
- Composition moves to `ExportReportWiring` (adds `create_docx_report_adapter(settings, logo_path)` reused by `create_use_case` and by test fixtures). The clock is injected as `Callable[[], datetime]` into header logo and footer.
- Indent steps for feedback items move to `DocxReportSettings` with defaults.
- Non-goals: no change to report text, order, colors or Spanish copy; no i18n extraction; no change to `ReportExportPort` or `ReportInputDTO`; no change to `JsonReportAdapter`.

## 4. Tasks

- [x] **TASK-01** Characterization safety net: a test that exports a full report with real `python-docx` and compares a fingerprint (ordered paragraph text, run bold/italic/size/color, table cells, header/footer text, with dates masked) against the current behavior; must pass on unchanged code. Test-only.
- [ ] **TASK-02** Extract shared writers (`DocxMarkdownRunWriter`, `DocxFeedbackBlockWriter`, `DocxSectionHeadingWriter`, `DocxLabeledParagraphWriter`, `CitationMatchRateFormatter`) with their own tests; adapter delegates to them; migrate the feedback-blocks tests; remove the duplicated code from the adapter.
- [ ] **TASK-03** `DocxReportSection` ABC plus sections group A (title page, document info, classification, editorial suitability, structure validation, citations analysis, footer), each with tests migrated from the private-method tests; adapter delegates to them.
- [ ] **TASK-04** Sections group B (executive summary, quality analysis, grammar analysis, APA validation, recommendations) with module-level constants for the verdict colors and priority icons, settings-driven indent, tests migrated.
- [ ] **TASK-05** `DocxPageDecoration` ABC plus `DocxBaseStyleDecoration`, `DocxHeaderLogoDecoration` (no inline comment, explicit unreadable-logo handling), `DocxPageNumberDecoration`; clock injection; tests.
- [ ] **TASK-06** Reduce `DocxReportAdapter` to the thin orchestrator, compose in `ExportReportWiring.create_docx_report_adapter`, update `ReportFixtures`, delete the migrated private-method tests and dead code.
- [ ] **TASK-07** Verification: `pytest src/ tests/`, `ruff check src/`, characterization test unchanged, grep audit for `#` comments, abbreviations, `Any`, local imports, `import x` style, and import-direction invariants.

## 5. Evidence

(commit identities and observed checks are recorded here per task)

- Baseline before TASK-01 (2026-10-07): `pytest` of the docx/report/wiring tests: 47 passed.
- TASK-01 done and verified by the parent (2026-10-07): characterization test (`DocxFingerprintBuilder`, golden `docx_report_fingerprint.json`, determinism guard). Report/wiring tests: 49 passed (47 + 2 new), ruff clean, golden has 4 masked dates and no raw timestamps. Full `pytest src/ tests/` cannot collect in this environment because `markupsafe` is not installed (pre-existing, unrelated); regression net for this feature = docx/report/wiring tests. The pi-lens `python-hallucinated-import` warning on `from unittest import TestCase` is a false positive. Commit: see git log (`test(report): add docx export characterization test`).
