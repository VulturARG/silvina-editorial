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
- [x] **TASK-02** Extract shared writers (`DocxMarkdownRunWriter`, `DocxFeedbackBlockWriter`, `DocxSectionHeadingWriter`, `DocxLabeledParagraphWriter`, `CitationMatchRateFormatter`) with their own tests; adapter delegates to them; migrate the feedback-blocks tests; remove the duplicated code from the adapter.
- [x] **TASK-02B** Rule compliance (user decision 2026-10-11: no task may defer a rule violation): `ExportReportWiring` builds every adapter collaborator and the clock, `DocxReportAdapter` instantiates nothing; inject `clock: Callable[[], datetime]` and remove every `datetime.now()`; remove the inline comment and the swallowing `try/except` in the header logo (user chose option B: guard clause checks the logo file is readable, skips only the picture and logs a warning); rename abbreviations; type every `document` parameter as `DocxDocument`; docstring on `export`; centralize adapter construction in `ReportFixtures.make_adapter`; characterization fingerprint unchanged.
- [ ] **TASK-03** `DocxReportSection` ABC plus sections group A (title page, document info, classification, editorial suitability, structure validation, citations analysis, footer), each with tests migrated from the private-method tests; adapter delegates to them.
- [ ] **TASK-04** Sections group B (executive summary, quality analysis, grammar analysis, APA validation, recommendations) with module-level constants for the verdict colors and priority icons, tests migrated (settings-driven feedback indent moved to TASK-02).
- [ ] **TASK-05** `DocxPageDecoration` ABC plus `DocxBaseStyleDecoration`, `DocxHeaderLogoDecoration`, `DocxPageNumberDecoration` (logo handling and clock injection already done in TASK-02B); tests.
- [ ] **TASK-06** Reduce `DocxReportAdapter` to the thin orchestrator, compose the new sections and decorations in `ExportReportWiring` (collaborator composition started in TASK-02B), delete the migrated private-method tests and dead code.
- [ ] **TASK-07** Verification: `pytest src/ tests/`, `ruff check src/`, characterization test unchanged, grep audit for `#` comments, abbreviations, `Any`, local imports, `import x` style, and import-direction invariants.

## 5. Evidence

(commit identities and observed checks are recorded here per task)

- Baseline before TASK-01 (2026-10-07): `pytest` of the docx/report/wiring tests: 47 passed.
- TASK-01 done and verified by the parent (2026-10-07): characterization test (`DocxFingerprintBuilder`, golden `docx_report_fingerprint.json`, determinism guard). Report/wiring tests: 49 passed (47 + 2 new), ruff clean, golden has 4 masked dates and no raw timestamps. Full `pytest src/ tests/` cannot collect in this environment because `markupsafe` is not installed (pre-existing, unrelated); regression net for this feature = docx/report/wiring tests. The pi-lens `python-hallucinated-import` warning on `from unittest import TestCase` is a false positive. Commit: see git log (`test(report): add docx export characterization test`).
- TASK-02 done and verified by the parent (2026-10-07): extracted `DocxMarkdownRunWriter`, `DocxFeedbackBlockView`, `DocxFeedbackBlockWriter`, `DocxSectionHeadingWriter`, `DocxLabeledParagraphWriter`, `CitationMatchRateFormatter`; new setting `feedback_item_indent_inches`; adapter delegates (10 heading sites, 17 labeled-paragraph sites replaced). Old `test_docx_report_adapter_feedback_blocks.py` deleted by the parent after its cases were migrated. Report/wiring tests: 79 passed, characterization unchanged and green, ruff clean, no inline comments/`Any`/local imports in the new files. Note: `DocxFeedbackBlockView.from_block` adds defensive `str()`/`int()` coercions that the original code did not have (harmless). Adapter is still 593 lines until TASK-03 to TASK-06. Commit: pending user authorization.
- TASK-02 refinement (2026-10-07, user request: replace if/elif chains with better practices): `DocxFeedbackBlockWriter` dispatches by `FeedbackBlockKind.value` through a mapping (no if/elif, no try/except); `DocxFeedbackBlockView` reads fields through one `_read_field` (Mapping or getattr) and the extra `str()`/`int()` coercions were removed; `DocxMarkdownRunWriter` uses one generic `_iter_pattern_segments` generator and one `_add_styled_run` helper. Report/wiring tests: 97 passed, characterization unchanged, ruff check and format clean. Review is NOT to be launched until the branch is finished and the user authorizes it. Commit: still pending user authorization.
- TASK-02 typing fix (2026-10-11, user request after review): `DocxFeedbackBlockView` no longer uses `Any`/`isinstance`/`getattr`; new `DocxFeedbackBlockPayload` TypedDict types the serialized block; `kind` is `FeedbackBlockKind` (unknown or missing -> `TEXT`), so `DocxFeedbackBlockWriter` indexes its enum-keyed mapping directly. Removed speculative DTO/`SimpleNamespace` inputs (production only passes dicts from `QualityAnalyzer`). Report tests: 87 passed (report + wiring: 146), ruff check/format clean, pyright 0 errors on the touched files. Commit: still pending user authorization.
- TASK-02B done and verified by the parent (2026-10-11): adapter receives 7 injected collaborators plus `clock`, instantiates nothing; `ExportReportWiring` has one private method per dependency (public `create_use_case` kept, FastAPI depends on it); header/footer dates from `self._clock()`; logo: guard clause `isfile and access(R_OK)` skips only the picture and logs a warning (no try/except, no inline comment); abbreviations renamed; `document: DocxDocument` on every `_add_*`; `export` docstring; `ReportFixtures.make_adapter`; new tests for header logo (4) and clock. `.venv` tests: 115 passed, ruff check/format clean, golden unchanged, no `datetime.now`/`#`/abbreviations in the adapter. Characterization test changed only its construction line. `from __future__ import annotations` needed for the guarded docx imports. Pre-existing Pyright "possibly unbound" warnings from the try/except ImportError pattern remain. Commit: pending user authorization.
