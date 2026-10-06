# Feature: Feedback Italics, Bullet Indent and Dimension Label

- **Feature Name**: `feedback-italics-indent-label`
- **File Locator**: `odd/tasks/feedback-italics-indent-label.md`
- **Branch**: `fix/feedback-title-and-bullet-indent` (continues the branch; the feedback parser and CSS live only here)
- **TDD Mode**: Enabled (RED -> GREEN -> REFACTOR) where a runnable test applies
- **TDD Runner**: `.venv/Scripts/python -m unittest discover -s src -t . -p "test_*.py"` with `USE_EXTERNAL_LLM=false APP_MODE=PROD`
- **Delivery Strategy**: `ask-on-risk`

---

## 1. Objective

Three defects seen by the user in the web page and the `.docx` of the Claude haiku run on 2026-10-04 (report `analisis (13)`):

1. Bullets that follow a lead-in paragraph ("El texto presenta tres lineas:") are indented one step more than bullets placed directly under a title.
2. Emphasis written with one asterisk (`*correctamente*`, `*mecanismo*`, `*cual*`) is shown with literal asterisks in the web page and in the `.docx`; only `**bold**` is interpreted.
3. The dimension title shows `Argumentacion` without the accent. The word comes from `QualityDimension.ARGUMENTATION = "argumentacion"`, which is also the key of `dimension_scores` in the JSON report, and both renderers print it with `capitalize()`.

## 2. Scope

### In scope
- F-G: in `FeedbackStructureParser`, the items that follow a lead-in paragraph (the "unindented children" mode) keep level 0; an item indented deeper than the first child becomes level 1. Items nested by the source indentation keep their level.
- F-H: `*text*` renders as italic in `InlineBoldRenderer` (web) and in `DocxReportAdapter._add_markdown_paragraph` (`.docx`); `**text**` keeps rendering as bold and the two do not interfere. A lone `*` (list marker, `a * b`, footnote mark) stays literal. The recommendation text (`DimensionRule._clean_feedback`) drops the single-asterisk markers as it already drops `**`.
- F-I: the user-facing title of a dimension comes from a label ("Argumentacion" -> "Argumentación"). The data key `argumentacion` is NOT changed because it is part of the JSON report. Web, `.docx` and the recommendation message use the label.

### Out of scope
- The 120-character cut of the editorial suitability fields, the "APTO" verdict wording and the recommendation that dumps the whole conclusions paragraph (product decisions, pending the user).
- Renaming `InlineBoldRenderer` and the `inline_bold` template filter (the name becomes narrower than the behavior; recorded as a follow-up).

## 3. Tasks

- [x] **TASK-01** F-G in `FeedbackStructureParser` + tests (existing tests that pin level 1/2 for lead-in children are updated to 0/1). RED first.
- [x] **TASK-02** F-H single-asterisk italics: `InlineBoldRenderer`, `DocxReportAdapter._add_markdown_paragraph`, `DimensionRule._clean_feedback`, with tests in each layer. RED first.
- [x] **TASK-03** F-I dimension label: domain label lookup on `QualityDimension` (unknown keys fall back to `capitalize()`), a Jinja filter registered in `dependencies.py`, `_results.html`, `DocxReportAdapter` and `DimensionRule`; tests. RED first.

## 4. Evidence

Implemented by one `gentle-ai-worker` (test-first) and verified by the parent on 2026-10-04.

- **RED**: TASK-01 12 failures (levels pinned to 1/2 in `test_feedback_structure_parser.py` and `test_quality_response_parser.py`, plus the new lead-in test); TASK-02 6 failures (renderer, docx runs, recommendation text); TASK-03 12 failures plus 2 `AttributeError` (no label lookup, template and docx heading still `Argumentacion`).
- **GREEN**: full suite `USE_EXTERNAL_LLM=false APP_MODE=PROD .venv/Scripts/python -m unittest discover -s src -t . -p "test_*.py"`: 1242 tests OK (baseline 1230). `ruff check src` and `ruff format --check src` clean; LF endings; no inline comments added.
- **Real data** (parent, stored Claude haiku responses ai_interactions 100 and 101): every item of the four dimensions is level 0; the three phrases `*correctamente*`, `*mecanismo*` and `*cuál*` render as `<em>` and no literal asterisk is left in any block; the Argumentación title comes from `QualityDimension.label_for`.
- **Decision**: the data key `argumentacion` is unchanged (it is part of the JSON report); only the displayed label carries the accent.
- **Commits**: TASK-01 alone; TASK-02 and TASK-03 together because they share `docx_report_adapter.py`, `dimension_rule.py` and their tests.
- **Follow-up**: `InlineBoldRenderer` and the `inline_bold` filter now render italics too; renaming them is pending.
