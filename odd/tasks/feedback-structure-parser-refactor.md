# Feature: FeedbackStructureParser Refactor

- **Feature Name**: `feedback-structure-parser-refactor`
- **File Locator**: `odd/tasks/feedback-structure-parser-refactor.md`
- **Branch**: `refactor/feedback-structure-parser` (from `silvina_editorial_v100` at `c93d188`)
- **TDD Mode**: Behavior-preserving refactor: the existing tests are the safety net; every new class gets its own tests first (RED -> GREEN)
- **TDD Runner**: `export USE_EXTERNAL_LLM=false APP_MODE=PROD; .venv/Scripts/python.exe -m unittest discover -s src -t . -p "test_*.py"` (baseline 1242 tests OK)
- **Delivery Strategy**: `ask-on-risk`

---

## 1. Objective

Break `FeedbackStructureParser` (350 lines) into small single-purpose classes without changing its output. The user's review (2026-10-04): the class does not follow SOLID, `parse` is a pile of nested `if`s and long.

Measured on `silvina_editorial_v100`:

| Method | Lines | Complexity | Nesting | Exits |
|---|---|---|---|---|
| `parse` | 188 | 41 | 4 | 13 |
| `_cap_and_filter_sections` | 45 | 11 | 6 | 1 |
| `_is_plain_line_title` | 28 | 12 | 1 | 11 |
| `_line_starts_unindented_children` | 18 | 5 | 1 | 5 |

Smells found:
- SRP: one class prepares lines, classifies them, tracks the hierarchy, builds sections and caps them.
- OCP: a new line kind forces an edit of `parse`.
- DIP: `QualityResponseParser` builds `FeedbackStructureParser()` itself when none is given.
- `parse`: 8 mutable locals acting as a state machine; the "open a title" block is repeated 3 times (heading, bold title, plain title); the bullet and numbered branches are identical but for the marker; the children-mode reset is repeated 4 times; `break` in the middle of the loop; `previous_line_counts_as_blank` is set in some branches and not in others.
- `_cap_and_filter_sections`: 6 levels of nesting, 3 counters/flags, mixes capping with dropping empty titles, and the `level >= 2` branch is dead code since the parser only produces levels 0 and 1.
- `_is_plain_line_title`: 10 chained guards written as `if`s; two are redundant because `parse` already resolved headings and bold titles; hidden dependence on the call order.
- `_line_starts_unindented_children`: a flag argument (`is_list_item`) computed by the caller; `replace("**", "")` recomputed.
- `_is_list_item` / `_find_next_non_empty_line` / `_prepare_lines`: the same regexes evaluated two or three times per line; anonymous `tuple[str, int]`.
- `_clean_title_text`: the trailing `:` is stripped twice, order-sensitive.
- Primitive obsession: `tuple[str, int]`, `tuple[FeedbackBlockDTO | None, list[...]]`; the marker `"•"` is a literal.

## 2. Scope

### In scope
- Same public contract: `FeedbackStructureParser.parse(lines, dimension_heading_level) -> tuple[FeedbackBlockDTO, ...]`, same output for every input.
- Constructor injection (decided by the user on 2026-10-04): `FeedbackStructureParser` receives its collaborators with no defaults; `AnalyzeDocumentUseCaseWiring` assembles them; `QualityResponseParser` stops building `FeedbackStructureParser()` itself; tests build the parser through one test helper.
- Remove the dead `level >= 2` branch of the capping.

### Out of scope
- Any change of behavior (levels, titles, caps, text cleaning), the web/docx renderers, the other parsers.
- Heuristic tuning of what counts as a plain title.

## 3. Safety net

1. The 837-line `test_feedback_structure_parser.py`, `test_quality_response_parser.py` and the rest of the suite: 1242 tests OK before the refactor.
2. Characterization snapshot over the 38 stored `quality_analysis` responses (`data/metrics.db`) x caps 2, 5 and 8 = 114 variants, 1624 blocks, scores, feedback and blocks (kind, text, level, marker). Script and baseline outside the repo: `%TEMP%\feedback_golden.py` and `%TEMP%\feedback_golden_before.json`, sha256 `6e171913ec34b722` (deterministic across two runs). After the refactor the same script must produce a byte-identical file. The script builds the parser through `src/domain/tests/quality/feedback_structure_parser_builder_for_test.py` (class `FeedbackStructureParserBuilderForTest`, method `build(maximum_items_per_section: int = 8)`) when the old constructor no longer works.

## 4. Design (final; the first proposal changed in two review passes, see Evidence)

- `FeedbackLineDTO` (text, indentation) replaces `tuple[str, int]`.
- `FeedbackLineKind` enum: heading, bold title, plain title, bullet, numbered, table row, horizontal rule, text.
- `FeedbackLineClassifier`: turns the prepared lines into classified lines (needs the previous-blank state and the next non-empty line); the plain-title rules become a list of small predicates.
- `FeedbackHierarchyTracker`: previous top-level indentation, children mode and child indentation; one place for the reset.
- `FeedbackSectionCapper`: the capping, without dead code.
- `FeedbackTextCleaner`: title and dangling-bold cleaning.
- `FeedbackStructureParser.parse`: orchestration (~30 lines), dispatching by line kind instead of an `if` chain.

## 5. Tasks

- [x] **TASK-01** Collaborators with their own tests, each behavior copied from the current private methods: `FeedbackLineDTO`, `FeedbackLineKind`, `FeedbackTextCleaner`, `FeedbackSectionCapper` (dead branch removed, proven by a test that levels above 1 do not exist), `FeedbackHierarchyTracker`, `FeedbackLineClassifier`. `FeedbackStructureParser` is not touched yet. RED first.
- [x] **TASK-02** Rewrite `FeedbackStructureParser` on top of them with constructor injection (no defaults); add `FeedbackStructureParserBuilderForTest`; migrate the 45 constructions in `test_feedback_structure_parser.py` and the other tests to the helper. The existing tests must pass unchanged in their assertions.
- [x] **TASK-03** Wiring: `AnalyzeDocumentUseCaseWiring` assembles the collaborators and the parser; `QualityResponseParser` receives the parser without building one (drop the `or FeedbackStructureParser()` default and fix its callers/tests).
- [x] **TASK-04** Verify: full suite, `ruff`, snapshot byte-identical to the baseline, complexity/lines of the new `parse` measured again.

## 6. Evidence

Implemented by one `gentle-ai-worker` in three passes; the parent verified each pass independently (golden, suite, ruff, line endings, inline comments, domain purity, code read) and rejected the first two.

### Final design
- Stateless, injected and shared: `FeedbackLineClassifier` (prepares and classifies lines in one regex pass into `ClassifiedFeedbackLineDTO`, including `starts_unindented_children`), `FeedbackSectionCapper`, `FeedbackTextCleaner`.
- Per-call state, created inside each `parse()`: `FeedbackParsingState` owning `FeedbackSectionAccumulator` and `FeedbackHierarchyTracker`; `FeedbackSectionCapState` is created per section inside the capper.
- Other new types: `FeedbackLineDTO`, `ClassifiedFeedbackLineDTO`, `FeedbackLineKind`, `FeedbackListMarker` (bullet marker and numbered format).
- `FeedbackStructureParser(classifier, capper, text_cleaner)`: the constructor stores the collaborators and builds the kind -> handler table; handlers take `(line, state)` and return `None`.
- Wiring: `AnalyzeDocumentUseCaseWiring` assembles the parser and `QualityResponseParser` (`feedback_structure_parser` is required). Tests use `FeedbackStructureParserBuilderForTest` and `QualityResponseParserBuilderForTest`.

### Review passes
1. Pass 1 met the numeric targets but kept the smells: state threaded through parameters and tuple returns, integers used as booleans, unused parameters, regexes evaluated twice, `starts_unindented_children` in the tracker taking the line kind as a flag, pass-through wrapper and a literal marker. Rejected.
2. Pass 2 fixed those. The parent then found a real defect introduced by the refactor: the injected `FeedbackHierarchyTracker` kept mutable state while the web app keeps one module-level `AnalyzeDocumentUseCase` and runs each analysis in a worker thread, so two simultaneous analyses would share it. Before the refactor that state was local to `parse()`.
3. Pass 3 moved the hierarchy state to per-call objects and added isolation and thread-pool tests (RED reproduced against the previous design: `vars(parser._hierarchy_tracker)` changed after `parse()`); it also removed the 5-parameter threading from the capper.

### Metrics (`parse`)
| | Before | After |
|---|---|---|
| Lines | 188 | 22 |
| Complexity | 41 | 4 |
| Nesting | 4 | 2 |
Every method of the new classes: complexity at most 6, nesting at most 2, at most 3 parameters besides `self`, no boolean flag parameter. The dead `level >= 2` branch of the capping is gone.

### Verification (parent)
- Suite: `USE_EXTERNAL_LLM=false APP_MODE=PROD .venv/Scripts/python -m unittest discover -s src -t . -p "test_*.py"`: 1302 tests OK (baseline 1242). `ruff check` and `ruff format --check` clean; LF endings; no inline comments; no import from `application/` or `infrastructure/` in the domain files; concurrency test run 15 times without a failure.
- Characterization: the 38 stored `quality_analysis` responses x caps 2, 5 and 8 (114 variants, 1624 blocks) produce a byte-identical snapshot, sha256 `6e171913ec34b722`, before and after each pass.

### Notes
- The snapshot covers real model outputs only; edge cases are covered by the unit tests migrated without changing assertions (837 lines) and by the new tests of each class.
- Open for the user: other classes in the same package may deserve the same review (`QualityResponseParser`, `EditorialSuitabilityParser`).
