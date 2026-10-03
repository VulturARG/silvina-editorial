# Feature: Feedback Review Follow-ups

- **Feature Name**: `feedback-review-followups`
- **File Locator**: `odd/tasks/feedback-review-followups.md`
- **Branch**: `fix/feedback-review-followups` (from `silvina_editorial_v100`)
- **TDD Mode**: Enabled (RED -> GREEN -> REFACTOR)
- **TDD Runner**: `.venv/Scripts/python -m pytest src/`
- **Delivery Strategy**: `ask-on-risk`

---

## 1. Objective

Close the four non-blocking findings that the native reviews of `feedback-markdown-and-sentence-split` left as follow-ups (lineages `review-e20dc59235ef9d48` and `review-d2763e21e9fa59ec`). Ordered by the user on 2026-10-03: "Hagamos Seguimientos menores de las revisiones del feedback con el procedimiento habitual".

## 2. Scope

### In scope
- F-A: a short plain line ending in `:` and followed by a list always opens a new section, even inside a section (an inline `Por ejemplo:` resets the cap).
- F-B: `FeedbackStructureParser` looks for the next non-empty line by slicing the rest of the list on every line (quadratic in the number of lines).
- F-C: `EditorialSuitabilityParser`: `LINEAS:` followed by a blank line and then the list returns an empty value.
- F-D: `EditorialSuitabilityParser`: a sentence that ends in a number of one or two digits followed by an uppercase word (`en la línea 4. Otra oración`) is not cut.

### Out of scope
- Hanging indent of the bullets in the web page (cosmetic).
- A column for the structure type in the metrics.

## 3. Evidence that drives the rules

- F-A: in the 24 stored quality responses of `ai_interactions` (all models) there are 19 plain lines that end in `:`, have at most 60 characters, have no sentence punctuation and are followed by a list item; all 19 are preceded by a blank line (or are the first line of the block). So a plain title can require a blank line before it without losing any real title.
- F-D: the list-number rule of `EditorialSuitabilityParser` skips any period that follows one or two digits preceded by whitespace. Real list numbers appear at the start of the text or right after `;` (Gemma, `ai_interactions` 77: `3. Recursos humanos…; 4. Dinámica…; 7. Ciencia…`).

## 4. Tasks

- [x] **TASK-01** F-A and F-B in `FeedbackStructureParser`: a plain-line title needs a blank line before it (or to be the first non-empty line of the block); an index-based search for the next non-empty line. Tests first. Done: RED 2 failing first; the parser prepares the stripped lines and their indentation once and looks ahead by index; a 2000-line block parses in about 0.007 s with the same result as the small one. UNCOMMITTED.
- [x] **TASK-02** F-C and F-D in `EditorialSuitabilityParser`: blank lines allowed between the `LINEAS:` label and its list; a period belongs to a list number only when the digits start the text or follow `;`, `,`, ` Done: RED 3 failing first; `LINEAS:` with blank lines before the list is captured, `en la línea 4. Otra oración` is cut after `4.`, and the Gemma shape (`3. …; 4. …; 7. …`) still returns the three numbered lines. UNCOMMITTED.

## 5. Evidence

(commit identities and observed checks are recorded here per task)
- Verified by the parent (2026-10-03): `pytest src/ tests/` 1253 passed, ruff clean. Regression check on the stored responses: the block structure of 18 quality responses (every dimension, titles, kinds, levels, markers, texts) and the fields of 18 suitability responses (`ai_interactions`) parsed with `HEAD` (extracted with `git archive` to a temporary directory) and with the working tree produce the same digest, so the four fixes change nothing for the real responses stored so far.
