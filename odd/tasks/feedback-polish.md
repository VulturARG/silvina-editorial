# Feature: Feedback Polish (title under a heading, hanging indent)

- **Feature Name**: `feedback-polish`
- **File Locator**: `odd/tasks/feedback-polish.md`
- **Branch**: `fix/feedback-title-and-bullet-indent` (from `silvina_editorial_v100`)
- **TDD Mode**: Enabled (RED -> GREEN -> REFACTOR) where a runnable test applies
- **TDD Runner**: `.venv/Scripts/python -m pytest src/`
- **Delivery Strategy**: `ask-on-risk`

---

## 1. Objective

Two of the pending items left after `feedback-review-followups`, ordered by the user on 2026-10-03 ("Encaremos todos los pendientes"). The other two pending items are separate work: the structure type in the metrics (branch `feat/analysis-structure-type`) and a native review of the two commits of the follow-ups that were not covered (`734536f`, `ec3f20f`).

## 2. Scope

### In scope
- F-E (review finding R3-003): a plain label such as `Fortalezas:` directly under a `###` heading with no blank line between them is not read as a title, because a heading clears the "previous line was blank" state; its items become children of a text block.
- F-F: in the web page the second line of a bullet starts under the bullet instead of under the text (no hanging indent).

### Out of scope
- The metrics column for the structure type and the native review of the merged commits.

## 3. Tasks

- [x] **TASK-01** F-E in `FeedbackStructureParser`: a title line (heading or bold-only line) leaves the parser in the same state as a blank line, so a plain label right below it can be a title; a plain label right below a table row or a text line is still not a title. Tests first, including the exact shape (`### Fortalezas` is NOT involved: use a heading such as `### Análisis` followed directly by `Fortalezas:` and bullets).
- [x] **TASK-02** F-F in `silvina.css`: hanging indent for `.feedback-block-item` at the three levels, with a marker of fixed minimum width so that numbers such as `10.` do not break the alignment; no change of markup unless it is needed. A template test that pins the structure the CSS relies on.

## 4. Evidence

(commit identities and observed checks are recorded here per task)

- Done and verified by the parent (2026-10-03): TASK-01: heading and bold-only title lines leave the parser in the state of a blank line (`previous_line_counts_as_blank`), so `### Análisis` followed directly by `Fortalezas:` and bullets gives the plain title with its items; the heading with no items of its own is dropped by the existing rule; a plain label directly under a table row or a text line is still not a title; RED 2 failing first. TASK-02: hanging indent in `silvina.css` with the custom properties `--feedback-marker-width` (1.4em) and `--feedback-indent-step` (16px): the marker is an inline-block with that minimum width, each item has `padding-left` equal to the marker width plus its level step and a `text-indent` of minus the marker width, so wrapped lines start under the text; text blocks get no hanging indent; no markup change; RED 1 failing first (the stylesheet test). `pytest src/ tests/` 1261 passed, ruff clean. The block structure of the 18 stored quality responses is identical with HEAD. The browser rendering was not seen by the parent: to be confirmed by the user on the web page. UNCOMMITTED.
