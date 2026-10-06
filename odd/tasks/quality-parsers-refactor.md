# Feature: QualityResponseParser and EditorialSuitabilityParser Refactor

- **Feature Name**: `quality-parsers-refactor`
- **File Locator**: `odd/tasks/quality-parsers-refactor.md`
- **Branch**: `refactor/quality-parsers` (from `silvina_editorial_v100` at `1481c0a`)
- **TDD Mode**: Behavior-preserving refactor: the existing tests are the safety net; every new class gets its own tests first (RED -> GREEN)
- **TDD Runner**: `export USE_EXTERNAL_LLM=false APP_MODE=PROD; .venv/Scripts/python.exe -m unittest discover -s src -t . -p "test_*.py"` (baseline 1302 tests OK)
- **Delivery Strategy**: `ask-on-risk`
- **Commit policy**: no commits until the user says so (order of 2026-10-04); authorized later the same day together with push, PR and merge

---

## 1. Objective

Apply to `QualityResponseParser` and `EditorialSuitabilityParser` the same SOLID/smell review done on `FeedbackStructureParser` (PR #69). Scope chosen by the user on 2026-10-04: the complete refactor (typed results and enums included), not the narrow one.

Measured on `silvina_editorial_v100` (`%TEMP%\method_metrics.py`):

| Method | Lines | Complexity | Nesting |
|---|---|---|---|
| `QualityResponseParser.parse` | 30 | 7 | 2 |
| `QualityResponseParser._extract_feedback_and_blocks` | 18 | 4 | 1 |
| `EditorialSuitabilityParser._extract_lines_field` | 34 | 10 | 3 |
| `EditorialSuitabilityParser._is_list_number_period` | 21 | 12 | 1 |
| `EditorialSuitabilityParser._extract_first_sentence` | 15 | 5 | 2 |

Smells found:

`QualityResponseParser`
- SRP: one class splits blocks, maps the dimension, extracts the score (explicit and narrative inference), extracts and flattens feedback.
- `parse` keeps two parallel structures (`scores` and `matched_dimensions`) and two `continue`s; the rule "an empty candidate never replaces a dimension that already has blocks" is implicit.
- `len(feedback) < 10` is a magic number; the heading level is parsed inline; `_extract_feedback_and_blocks` returns an anonymous tuple.
- `except ValueError` in `_extract_score` is dead: the regex guarantees a parsable float.
- The dimension mapping depends on the order of the keyword table (`"argumento"` lands in CLARITY) and nothing declares it.
- The unscored placeholder (score and feedback) is two loose constructor floats/strings.

`EditorialSuitabilityParser`
- Verdicts are loose strings; `"NO SUSTENTADA"` and `"PARCIAL"` are duplicated between the candidate tuples and `_build_contribution_observation`; `_extract_verdict` depends on the tuple order (`"NO SUSTENTADA"` contains `"SUSTENTADA"`) and on `candidates[0]` as an implicit default.
- Both public methods return anonymous `tuple[str, str, str]`.
- Four near-identical label regexes; `.replace("**", "").lstrip("* :").strip()` copied three times.
- `_extract_lines_field`: label lookup, same-line value, first line after the label and list parsing in one method, with a `has_started_list` flag.
- `_is_list_number_period` walks indices by hand with magic numbers.
- Building the Spanish observation is presentation, not parsing.
- Length limits are module constants; the 120-character cut cannot be changed without editing the parser.

## 2. Scope

### In scope
- Same output for every input: the contract that changes is typing only (enum verdicts, result DTOs), and `EditorialSuitabilityDTO` keeps its string fields (JSON/template/docx contract).
- Constructor injection with no defaults; wirings assemble; tests use builders.
- Injected collaborators are STATELESS (the web app has one module-level `AnalyzeDocumentUseCase` and threads).

### Out of scope
- Any behavior change, including the pending decisions: the 120-character cut (the limits become constructor parameters but keep their values), APTO verdict wording, recommendation dumping, `InlineBoldRenderer` rename, `structure_type` column.
- `FeedbackStructureParser` and its collaborators.

## 3. Safety net

1. The existing suite: 1302 tests OK before the refactor.
2. Characterization snapshots, scripts and baselines outside the repo (`%TEMP%`), both deterministic across two runs:
   - `feedback_golden.py` -> `quality_golden_before.json`: 40 stored `quality_analysis` responses x caps 2/5/8 = 120 variants, 1717 blocks, sha256 `1efa81c450653493`.
   - `suitability_golden.py` -> `suitability_golden_before.json`: 38 stored `editorial_suitability` responses plus 25 synthetic edge cases (list numbers, decimals, bold labels, truncation boundaries 118/119/120, empty fields), `parse_contribution` and `parse_alignment` on each, sha256 `6f41286084e75c8b`.
   After the refactor each script must produce a byte-identical file (the suitability script normalizes the typed result back to strings).

## 4. Design

Suitability side (`src/domain/quality`, `src/domain/dtos`, `src/domain/enums`):
- `ContributionVerdict` and `AlignmentVerdict` enums (values are the current strings; members listed most specific first, order is significant and documented and tested).
- `ContributionAssessmentDTO(verdict, phrase, observation)` and `AlignmentAssessmentDTO(verdict, lines, justification)` replace the tuples; `EditorialSuitabilityAnalyzer` maps them to the unchanged `EditorialSuitabilityDTO` using the enum values.
- `SuitabilityFieldExtractor`: one label-pattern template, one value cleaner; verdict text, field value and same-line value.
- `SuitabilityVerdictMatcher`: raw verdict text -> enum member, first member as the documented default.
- `AlignmentLinesExtractor`: lines field (same line, first line after the label, list items) in small methods, no flag.
- `FirstSentenceExtractor` (list-number and decimal periods) and `SuitabilityFieldTruncator`.
- `ContributionObservationBuilder`: the fixed Spanish observations.
- `EditorialSuitabilityParser(...)`: orchestration only; limits (phrase, justification, lines) are constructor parameters, wiring passes the current values.

Quality side:
- `QualityDimensionMatcher`: block -> dimension, ordered table declared and tested.
- `DimensionScoreExtractor`: explicit score, narrative inference, clamping, no dead branch.
- `DimensionFeedbackExtractor(feedback_structure_parser, unscored_dimension)`: recommendation tail removal, heading level, structure parsing, flattening, minimum length; returns a `DimensionFeedbackDTO(feedback, blocks)`.
- One placeholder: `unscored_dimension: DimensionScoreDTO` injected into the parser and the two extractors.
- `QualityResponseParser.parse`: orchestration with a single dict of matched dimensions.

## 5. Tasks

- [x] **TASK-01** Suitability collaborators, enums and result DTOs with their own tests, each behavior copied from the current private methods. `EditorialSuitabilityParser` is not touched yet. RED first.
- [x] **TASK-02** Rewrite `EditorialSuitabilityParser` with constructor injection (no defaults); update `EditorialSuitabilityAnalyzer`, the wiring and the test wiring/builders; migrate the parser and analyzer tests to the typed results. Suitability snapshot byte-identical.
- [x] **TASK-03** Quality collaborators and `DimensionFeedbackDTO` with their own tests. `QualityResponseParser` is not touched yet. RED first.
- [x] **TASK-04** Rewrite `QualityResponseParser` on top of them; update wiring and `QualityResponseParserBuilderForTest`. Quality snapshot byte-identical.
- [x] **TASK-05** Verify: full suite, `ruff`, both snapshots, metrics measured again, docs.

## 6. Evidence

### TASK-01 and TASK-02 (suitability side), commit `b601565`

Implemented by one `gentle-ai-worker` in two passes; the parent verified each pass independently (golden, suite, ruff, line endings, inline comments, code read) and fixed the last smell inline.

- Pass 1 met every automatic check (golden byte-identical, 1378 tests OK, ruff clean) but a 60,000-case random differential test against the old parser from `git HEAD` (`%TEMP%\suitability_fuzz.py`, reinforced with tokens that produce empty list items) found a real behavior change: `AlignmentLinesExtractor` ended the list on a blank line even before a non-empty item had been collected (`'LÍNEAS:\n- **\n\n- two'` gave `''` instead of `'two'`; 14 mismatches). The golden snapshot did not cover it. `ContributionObservationBuilder` also accepted the enum or its raw string. Both sent back.
- Pass 2: three RED tests for the blank-line cases, strict enum comparison; fuzz `mismatches=0`.
- Inline by the parent: `_try_collect_item` mutated the list it received (state through parameters, a smell rejected in the previous refactor); replaced by the pure `_parse_list_item` returning `str | None`. Trade-off accepted: `_extract_list_items` complexity 6, nesting 3.
- Final: suite 1381 OK (baseline 1302), ruff clean, suitability snapshot byte-identical (sha256 `6f41286084e75c8b`), fuzz 60,000 cases 0 mismatches. `EditorialSuitabilityParser.parse_*` complexity 1, 12 and 15 lines; worst new method complexity 6 (was 12 in `_is_list_number_period`).
- New: enums `ContributionVerdict`, `AlignmentVerdict`; DTOs `ContributionAssessmentDTO`, `AlignmentAssessmentDTO`; `SuitabilityFieldExtractor`, `SuitabilityVerdictMatcher`, `AlignmentLinesExtractor`, `FirstSentenceExtractor`, `SuitabilityFieldTruncator`, `ContributionObservationBuilder`; `EditorialSuitabilityParserBuilderForTest`; wiring with named limit constants (120/120/200, observation 120).
- Lesson: a golden snapshot built from 38 real responses plus hand-picked cases does not prove equivalence; a differential fuzz against the old implementation does. Use both.

### TASK-03 and TASK-04 (quality side), commit `1f30254`

Implemented by one `gentle-ai-worker` in one pass, with the golden and a 12,000-response differential fuzz (`%TEMP%\quality_fuzz.py`, old parser from `git HEAD`, 11,811 cases with matched dimensions, 7,878 with two or more; a deliberate mutation of the clamp is caught with 3,506 mismatches) prepared by the parent before delegating. The parent verified independently and read the code.

- New: `QualityDimensionMatcher` (ordered keyword table documented), `DimensionScoreExtractor` (dead `except ValueError` dropped), `DimensionFeedbackExtractor`, `DimensionFeedbackDTO`; `QualityResponseParser(dimension_matcher, score_extractor, feedback_extractor, unscored_dimension)` with a single mapping of matched dimensions and the pure helper `_should_ignore_candidate`; one shared `unscored_dimension` placeholder assembled by the wiring (`_get_unscored_dimension`); `QualityResponseParserBuilderForTest` keeps its keyword arguments.
- Parent inline: removed a duplicated unscored result in `DimensionFeedbackExtractor.extract` (empty blocks format to an empty string, already under the minimum length); `ruff format` on one worker test file (a line wrap).
- A false alarm of the parent (CRLF check) was an artifact of the check script; `git ls-files --eol` shows LF everywhere.

### TASK-05 Final verification (tree at `1f30254`)

| Check | Result |
|---|---|
| Suite | 1420 tests OK (baseline 1302, +118) |
| `ruff check` / `ruff format --check` | clean / 491 files formatted |
| Quality snapshot | byte-identical, sha256 `1efa81c450653493` |
| Suitability snapshot | byte-identical, sha256 `6f41286084e75c8b` |
| Differential fuzz quality / suitability | 12,000 / 60,000 cases, 0 mismatches |
| Inline comments, local imports, endings | none, none, LF |

Metrics, worst method before -> after: `QualityResponseParser.parse` 30 lines complexity 7 -> 33 lines complexity 6 (it now also owns the single mapping of matched dimensions); `_extract_lines_field` 34 lines complexity 10 -> `_extract_list_items` complexity 6; `_is_list_number_period` 21 lines complexity 12 -> 2 lines complexity 1 (regex); `EditorialSuitabilityParser` methods 8-15 lines complexity 1. The real gain is structural: 4 responsibilities in `QualityResponseParser` and 6 in `EditorialSuitabilityParser` became 3 and 6 single-purpose stateless collaborators, verdicts are enums, results are DTOs, nothing is built inside the parsers.

Commits: `b601565` `refactor(suitability)` and `1f30254` `refactor(quality)`, then this `docs(odd)`. The shared files (`analyze_document_use_case_wiring.py` and its test) were split with hand-built intermediate versions so each commit stands alone: the suitability commit checked out in a clean worktree runs 1381 tests OK (it needs the git-ignored `.env`; without it 64 wiring/env tests error for that reason only).
