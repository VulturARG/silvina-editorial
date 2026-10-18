# Feature: Quality Score After the Analysis (Parser Support)

- **Feature Name**: `quality-score-after-analysis`
- **File Locator**: `odd/tasks/quality-score-after-analysis.md`
- **Branch**: `feat/quality-score-after-analysis` (from `silvina_editorial_v200`)
- **TDD Mode**: Enabled (RED -> GREEN -> REFACTOR) where a runnable test applies
- **TDD Runner**: `.venv/Scripts/python -m pytest -q src tests`
- **Delivery Strategy**: one work-unit commit per task on the feature branch; push, pull request and merge are requested explicitly by the user

---

## 1. Objective

Let the quality parser read a dimension whose score is written at the end, after the analysis, so a prompt can ask the model to reason first and score last. The behavior for the current layout (score in the dimension header) must not change.

## 2. Why

The quality prompts ask for `**1. Claridad** [Puntuación: X/10]` followed by the analysis, so the model commits to a number before any reasoning. Writing the score last would let the analysis condition it.

Checked on the real parser before this change (in memory, no files touched):

- Original layout (score in the bold header): scores and feedback are correct, and a `5/10` mentioned in the analysis does not override the header score.
- `### 1. Claridad del argumento` with `Puntuación: 8/10` as the last line: the dimensions are split correctly and the scores are right, but the score line stays inside the feedback shown in the report.
- A bold header without a score (`**1. Claridad del argumento**`): the block splitter does not recognize it, the next dimension is lost and its text is swallowed by the previous feedback. This layout stays unsupported on purpose.
- The score extractor takes the first score found in the block, so a number such as `5/10` written in the analysis before the final score line would win over it.

## 3. Agreed specification

- A dimension block uses the "score last" layout only when its first line (the header) carries no explicit score and its last non-empty line is a dedicated score line: only `Puntuación: X/10`, optionally with brackets, bold, a decimal score, a missing `/10` or a final period.
- In that layout the score is the one of the last line, clamped like today, and that line is removed from the feedback.
- In every other case the behavior is exactly the current one: the header score wins when present, a score line that is not the last line stays in the text, and the first explicit score is used as before.
- The logic lives in one new collaborator used by `QualityResponseParser`. `DimensionScoreExtractor` and `DimensionFeedbackExtractor` and their tests do not change.
- Only the parser changes in this feature. The v2 quality prompts keep their current format until this is merged.

## 4. Constraints

- Follow `.agent/skills/clean-architecture/SKILL.md`.
- The existing tests must keep passing without changing their expectations; only construction code of the parser may be adapted.
- No settings, no environment variables.

## 5. Tasks

- [x] **TASK-01** New collaborator that detects the "score last" layout and returns the score and the block without that line; `QualityResponseParser` uses it; builder and wiring updated. RED first.

## 6. Evidence

### TASK-01
- RED: 16 new tests failing (13 of the locator, 2 of the parser end to end, 1 of the wiring), observed with a stub locator that returned `None` and was not yet used by the parser. Eight tests that protect the current behavior (the locator returning `None` outside the layout, the header score winning over a stray last line) already passed, as expected.
- GREEN: baseline 2318 passed, final 2342 passed (187 subtests), re-run by the parent; `ruff check` and `ruff format --check` clean. No line of any pre-existing test was removed; the two modified test files only gained lines.
- The parent re-ran the in-memory experiment on the real parser: the original bold layout gives the same scores and feedback as before, including with `5/10` mentioned in the prose; the `###` layout with the score on the last line gives the right scores, no score line in the feedback, and ignores numbers written in the prose (`5/10`, `4/10`).
- `DimensionScoreExtractor`, `DimensionFeedbackExtractor` and the block splitter are untouched. A bold header without a score is still not supported.
