# Feature: Full-Text Body Refactor

- **Feature Name**: `full-text-body-refactor`
- **File Locator**: `odd/tasks/full-text-body-refactor.md`
- **Base branch**: `silvina_editorial_v200`; each task lives on its own branch from the base and is merged by pull request when the user orders it
- **Design**: `docs/full-text-refactor/04-design-options-and-task-plan.md` (decisions D1 to D7 approved by the user on 2026-10-15)
- **Commit policy**: from 2026-10-15 (TASK-04 onwards) the user ordered committing automatically at the end of each task and continuing with the next one; push, pull request and merge remain the user's decisions. Commits by type in this order: `docs`, then code (`feat`, `refactor`, `chore` or `fix`), then `test`. The code commit includes the minimal adjustments to existing tests so that the full suite passes in every commit; the test commit holds only new behavior tests, preferably in new test files.
- **Size rule**: at most about 400 lines per task, counted as added plus removed lines of non-test `.py` files under `src/` (`git diff --numstat`). `.toml`, tests, `.md` and `odd/` are not counted.

---

## 1. Objective

Make every analysis stage that uses an LLM, and the grammar check, read the whole article body (abstract included for grammar) instead of sampled excerpts. Remove the per-stage character limits. Keep a single maximum body size defined in the editorial norms; above it the article is rejected before any analysis.

## 2. Rules the implementation must follow

- Body: starts at the repeated title, ends before the bibliography header. Abstract, keywords, header (authors, affiliation, notes), tables and bibliography are excluded.
- Maximum: 75000 characters of body, in `editorial_norms.toml`, no environment override. Rejection message in Spanish, handled like a document over 25 MB.
- Markers come from `editorial_norms.toml`, never from constants in the code.
- Size ranges are measured over the body; `extra largo` behaves like `largo`.
- Deterministic stages and LLM output cuts are out of scope.

## 3. Tasks

- [x] **TASK-01: Editorial norms for the body** (about 80 to 120 lines): `[bibliography]` (`header_markers`, `header_max_length`) and `[article_length]` (`max_body_chars`) in `editorial_norms.toml`, their DTOs, `EditorialNormsDTO`, `EditorialNormsLoader` with validation, test builder support. No consumer yet. Verified on branch `refactor/editorial-norms-for-body`: 2128 tests pass (baseline 2119 plus 9 new), ruff clean, 70 production code lines (cap 400), mutation check (dropping `.lower()` in the marker normalization) caught by 2 tests. Commits: `c3c9f89` docs, `a05e8b6` feat (code commit alone: 2119 tests pass), `7cdfce9` test.
- [x] **TASK-02: `ArticleBodyDTO` and `ArticleBodyLocator`** (branch `refactor/article-body-locator`, stacked on `refactor/editorial-norms-for-body`) (about 130 to 170 lines): new files only, no consumer yet. Implemented with TDD: 15 new tests, 101 production lines (cap 400). One-off cross-check over the 30 sample documents: all located, body sizes identical to the independent manual calculation (for example `01_IMRyD_Cano_Martinez` 38937 characters, 1 abstract paragraph). Review found that the length boundary was untested (mutation `<=` to `<` passed); two boundary tests were added and now catch it. Known edge case, not guarded: a first paragraph that normalizes to empty text. Commits: `9923a62` feat, `13ce6eb` test, `a8aedaa` docs.
- [x] **TASK-03: Body in `DocumentContentDTO` and the extractor** (about 60 to 100 lines): new `body` field, `DocumentContentExtractor` uses the locator, wiring; remove the old `abstract` field, `_extract_abstract` and their tests. Verified on branch `refactor/document-content-body`: 2150 tests pass (including `tests/smoke` and `tests/e2e`), ruff clean, 44 production lines (cap 400); mutation check (nulling `body`) caught by 3 tests; the two report fixtures that passed `abstract=` were fixed by the orchestrator (one line each). Native review (medium risk, one reliability lens) approved with 6 non-blocking warnings (R3-001 to R3-006: `document_content_extractor.py:37`, `document_content_dto.py:18` and `:21`, and three test files); authority acknowledged and burned. Commits: `9323b51` docs, `1ec4371` refactor, `06f9210` test.
- [x] **TASK-04: `EXTRA_LONG` size and size on the body** (branch `refactor/extra-long-article-size`, stacked on `refactor/document-content-body`) (about 70 to 110 lines): `ArticleSize.EXTRA_LONG`, `ArticleBodyDTO.char_count`, `extra_long_max_chars` from the norms, classifier measures the body. Verified: 2162 tests pass (2150 before, 12 new; code commit alone 2150), ruff clean, 14 production lines (cap 400); mutation check (`<=` to `<` at the extra-long upper bound) caught by 2 tests. Smoke consequence: the scientific sample goes from `UNDEFINED` (26144 characters whole document) to `SHORT` (16705 characters body), only 705 above the `SHORT` lower bound. Native review not run: the consent envelope expired unanswered after 10 minutes. Commits: `a9bd31f` docs, `674726d` feat, `9a5a7ab` test.
- [x] **TASK-05: Maximum length check** (branch `refactor/article-length-check`, stacked on `refactor/extra-long-article-size`) (about 90 to 130 lines): `AnalysisStage.VALIDATE_ARTICLE_LENGTH`, `DocumentBodyTooLong` (Spanish message), `ArticleLengthChecker`, use case call, wiring. Verified: 2176 tests pass (2162 before, 14 new; code commit alone 2162), ruff clean, 57 production lines (cap 400); mutation check (`>` to `>=`) caught by 1 test. Native review (medium risk, one reliability lens) approved with 3 non-blocking findings (R3-001 `test_article_length_checker.py:14-16`, R3-002 `analyze_document_use_case_wiring.py:129`, R3-003 `analyze_document_use_case.py:32`); authority acknowledged and burned. Commits: `dc75e2a` docs, `ac65aba` feat, `75ff456` test.
- [x] **TASK-06: Classification reads the body** (branch `refactor/classification-reads-body`, stacked on `refactor/article-length-check`) (about 140 to 190 lines): `ArticleClassifier` sends `body.title` and the joined body paragraphs; `ArticleClassificationTextSampler`, its settings DTO, 4 `EnvConfig` attributes and the `[article_classification]` TOML section removed. Verified: 2166 tests pass (2176 before, 13 removed, 3 new; code commit alone 2163), ruff clean, 124 production lines changed (cap 400, mostly deletions); mutation check (only the first paragraph) caught by 2 of the 3 new tests; RED against the old sampler showed the 200000-character body cut to a 6018-character prompt. Native review (medium risk, one reliability lens) approved with 3 non-blocking findings on `article_classifier.py:68-69` (R3-001 to R3-003); authority acknowledged and burned. Commits: `9c1cc65` docs, `b850229` refactor, `fc5dec1` test. README line 162 (text sampling) is left for TASK-07, which removes the quality sampling it describes.
- [x] **TASK-07: Quality and suitability read the body** (branch `refactor/quality-reads-body`, stacked on `refactor/classification-reads-body`) (about 200 to 260 lines): `ArticleBodyDTO.text`, `QualityAnalyzer` sends `body.text` to both quality prompts and to the suitability analyzer and raises `QualityAnalysisFailed` without body; `QualityTextSampler`, its settings DTO, 8 `EnvConfig` attributes (the plan said 9: 1 of `[quality]` and 7 of `[quality_text_sample]`) and both TOML sections removed; README text-sampling line replaced. Verified: 2156 tests pass (2166 before, 19 removed, 9 new; code commit alone 2147), ruff clean, 165 production lines changed (cap 400, mostly deletions); mutation check (title dropped) caught by 4 of the 5 new analyzer tests; RED against the old sampler showed a 200005-character body cut to 99996 characters losing the last paragraph. Native review (medium risk, one reliability lens) approved with 3 non-blocking findings (`quality_analyzer.py:31-32`, `quality_analyzer.py:34`, `article_body_dto.py:17`); authority acknowledged and burned. Left in place on purpose: `ReferenceLineMarker` (only the removed sampler used it) and `SettingsValueResolver.read_string` (no production caller left); both keep their tests. Commits: `2ca0a84` docs, `4cbd54a` docs (README), `39c27a1` refactor, `eee1e06` test.
- [ ] **TASK-08: Grammar reads body plus abstract** (about 80 to 130 lines): remove `max_paragraphs`, `max_chars` and `max_errors`; wiring.

## 4. TASK-01 detail

- `editorial_norms.toml` gets:
  - `[bibliography]` with `header_markers = ["referencias", "bibliografía", "bibliography", "fuentes bibliográficas"]` and `header_max_length = 30`;
  - `[article_length]` with `max_body_chars = 75000`.
- New DTOs `BibliographyNormsDTO` and `ArticleLengthNormsDTO`; `EditorialNormsDTO` gets the fields `bibliography` and `article_length`.
- `EditorialNormsLoader` reads both sections, normalizes the markers (stripped, lowercase, without duplicates) and raises `EditorialNormInvalid` when `header_max_length` or `max_body_chars` is below 1.
- `build_editorial_norms_for_test` accepts overrides for the new fields.
- Done when: the real file loads into the complete DTO, the missing-section and invalid-value cases raise the existing error types, the full suite passes, and `ruff` is clean.

## 5. TASK-02 detail

- `ArticleBodyDTO` (`src/domain/dtos/article_body_dto.py`, frozen, extends `BaseDTO`): `title: str`, `abstract_paragraphs: tuple[str, ...]`, `paragraphs: tuple[str, ...]` (the body paragraphs after the title). No behavior yet.
- `DocumentBodyNotLocated(DocumentError)` in `src/domain/exceptions/document_errors.py`: raised when the repeated title is not found (editorial rule broken). English message, like the other document errors.
- `ArticleBodyLocator` (`src/domain/document/article_body_locator.py`, domain service, no port): constructor receives `AbstractNormsDTO`, `KeywordNormsDTO` and `BibliographyNormsDTO`; method `locate(paragraphs: list[str]) -> ArticleBodyDTO` over the clean, non-empty, stripped paragraphs.
- Rules, all driven by the norms, no marker constants in the code:
  - The first paragraph of the document is only a search key. The repeated title is the first later paragraph whose normalized text (lowercase, runs of whitespace, colons and periods collapsed to one space) starts with the normalized first paragraph. If none exists, raise `DocumentBodyNotLocated`.
  - The abstract heading is the first paragraph before the repeated title whose lowercase text, without trailing colon or whitespace, equals one of `abstract.section_keywords`. The abstract runs from the next paragraph until the first paragraph that starts (lowercase) with one of `keywords.section_markers`, or until the repeated title. Without a heading the abstract is empty.
  - The bibliography header is the first paragraph after the repeated title whose stripped lowercase text has at most `bibliography.header_max_length` characters and contains one of `bibliography.header_markers`. The body ends before it; without a header the body runs to the last paragraph.
  - `title` is the repeated title paragraph; `paragraphs` are the paragraphs between it and the bibliography header.
- Cross-check, not a committed test: a one-off script over the 30 documents of `sandbox/pack_1/inputs` and `sandbox/pack_2/inputs` must locate every one of them; the body character count (title and paragraphs joined with a single space) of `pack_2/inputs/01_IMRyD_Cano_Martinez.docx` should be about 38937 and the abstract should be one paragraph.
- Done when: new files only (no consumer, no wiring), the full suite passes, `ruff` is clean.

## 6. TASK-03 detail

- Branch `refactor/document-content-body`, stacked on `refactor/article-body-locator`.
- `DocumentContentDTO`: new field `body: ArticleBodyDTO | None = None`, set only by `DocumentContentExtractor`; the old `abstract` field is removed.
- `DocumentContentExtractor`: new constructor argument `article_body_locator: ArticleBodyLocator`; `extract_content` attaches `body` located from `paragraphs`. `DocumentBodyNotLocated` propagates (the editorial rule is broken). `paragraphs`, `char_count`, `title` and every other field stay as they are.
- `ParagraphContentAdapter`: drop the `abstract=` argument and `_extract_abstract`; drop the `abstract` pattern from `extraction_vocabulary.py` if nothing else uses it.
- `AnalyzeDocumentUseCaseWiring`: new private method that builds `ArticleBodyLocator` from the editorial norms and passes it to the extractor.
- Existing tests are adjusted minimally in the code commit (extractor constructor, abstract assertions, fixtures whose paragraphs lack a repeated title). Smoke parity tests under `tests/smoke` may compare the removed `abstract` field.
- New behavior tests in new files for the test commit: body attached, error propagated, other fields untouched, wiring builds the locator from the norms.
- All project input documents (`docs/sample-documents`, `tests/fixtures`) already contain the repeated title.

## 7. TASK-04 detail

- Branch `refactor/extra-long-article-size`, stacked on `refactor/document-content-body`.
- `ArticleSize.EXTRA_LONG = "extra_largo"`.
- `ArticleBodyDTO.char_count` (property): length of the title and the body paragraphs joined with a single space.
- `ArticleSizeThresholdsDTO.extra_long_max_chars`: the extra-long range is `long_max_chars < count <= extra_long_max_chars`; `ArticleSizeClassifier` returns `EXTRA_LONG` there. No new keys in `analysis_settings.toml`.
- `ArticleClassifier.classify` measures the size with `document_content.body.char_count`; a document without body raises `ClassificationFailed`. The IMRyD gate (`!= OUT_OF_RANGE`) already treats `EXTRA_LONG` like `LONG`.
- `AnalyzeDocumentUseCaseWiring` passes `editorial_norms.article_length.max_body_chars` as `extra_long_max_chars`.
- Done when: the full suite passes in every commit, `ruff` is clean, and new behavior tests (body count, extra-long boundaries, classifier uses the body, wiring takes the upper end from the norms) live in new test files.

## 8. TASK-05 detail

- Branch `refactor/article-length-check`, stacked on `refactor/extra-long-article-size`.
- `AnalysisStage.VALIDATE_ARTICLE_LENGTH = "validate_article_length"`, placed right after `EXTRACT_CONTENT` in the pipeline.
- `DocumentBodyTooLong(DocumentError)` in `document_errors.py`: Spanish message through `dict()` stating the body size and the maximum; handled by the existing `BaseSrcError` handlers like `DocumentTooLarge`.
- `ArticleLengthChecker` (`src/domain/document/article_length_checker.py`, domain service, no port): constructor receives `ArticleLengthNormsDTO`; `check(document_content)` raises `DocumentBodyTooLong` when `body.char_count` is above `max_body_chars` (the maximum itself is accepted) and `DocumentBodyNotLocated` when there is no body.
- `AnalyzeDocumentUseCase` receives `article_length_checker` and tracks the new stage after `EXTRACT_CONTENT`; nothing else runs when it raises. `AnalyzeDocumentUseCaseWiring` builds the checker from the editorial norms.
- Done when: the full suite passes in every commit, `ruff` is clean, and new behavior tests (checker boundary, message, stage order, use case stops before the citations stage, wiring) live in new test files.

## 9. TASK-06 detail

- Branch `refactor/classification-reads-body`, stacked on `refactor/article-length-check`.
- `ArticleClassifier` loses its `text_sampler` argument. The signal prompt receives `title=document_content.body.title` (the repeated title, sent once) and `text_sample=" ".join(document_content.body.paragraphs)`. The body guard already exists from TASK-04.
- Removed: `ArticleClassificationTextSampler` and its tests, `ClassificationTextSamplingSettingsDTO`, `EnvConfig.get_classification_text_sampling_settings`, the four `EnvConfig` attributes (`article_classification_sample_introduction_character_limit`, `..._conclusion_character_limit`, `..._fallback_character_limit`, `article_classification_bibliography_header_max_length`), the `[article_classification]` section of `analysis_settings.toml` and its entries in `CompleteTestSettings` and the settings tests.
- `AnalyzeDocumentUseCaseWiring._get_article_classifier` stops building the sampler.
- Done when: the full suite passes in every commit, `ruff` is clean, no reference to the removed names remains (`grep`), and new behavior tests (prompt receives the body title and joined body paragraphs, nothing is cut) live in a new test file.

## 10. TASK-07 detail

- Branch `refactor/quality-reads-body`, stacked on `refactor/classification-reads-body`.
- `ArticleBodyDTO.text` (property): the title and the body paragraphs joined with a single space; `char_count` becomes `len(self.text)`. The quality prompts only have a `{text_sample}` placeholder and the old sample started with the title, so the title is sent once, inside this text.
- `QualityAnalyzer` loses its `text_sampler` argument: it sends `document_content.body.text` to both prompts and passes the same text to `EditorialSuitabilityAnalyzer.analyze(text_sample=...)`. A document without body raises `QualityAnalysisFailed`.
- Removed: `QualityTextSampler` and its tests, `QualityTextSamplingSettingsDTO`, `EnvConfig.get_quality_text_sampling_settings`, the 9 `EnvConfig` attributes (`min_sample_word_count` and the 8 of `[quality_text_sample]`), the `[quality]` and `[quality_text_sample]` TOML sections and their entries in `CompleteTestSettings` and the settings tests; `AnalyzeDocumentUseCaseWiring` stops building the sampler.
- `README.md`: the "Text sampling" line (first 3500 characters plus last 2500) is replaced by a line saying the whole article body is analyzed.
- Done when: the full suite passes in every commit, `ruff` is clean, no reference to the removed names remains in `src`, tests, TOML or README, and new behavior tests (both quality prompts and the suitability analyzer receive the whole body text, nothing is cut, `ArticleBodyDTO.text`, missing body raises) live in new test files.

## 11. TASK-08 detail

- Branch `refactor/grammar-reads-body`, stacked on `refactor/quality-reads-body`.
- `ArticleBodyDTO.abstract_and_body_paragraphs` (property, `list[str]`): the abstract paragraphs, then the repeated title, then the body paragraphs (document order).
- `GrammarChecker.check_grammar` receives `document_content: DocumentContentDTO` instead of `paragraphs`; it raises `DocumentBodyNotLocated` when there is no body and passes `body.abstract_and_body_paragraphs` to the port. `AnalyzeDocumentUseCase` passes `document_content` to the stage.
- `LanguageToolAdapter` stops truncating: the text is all the paragraphs joined with a newline, and no cap on the number of errors. `LanguageToolSettings` keeps only `max_replacements`. Misspellings are still discarded.
- Removed: `max_paragraphs`, `max_chars` and `max_errors` from `LanguageToolSettings`, `EnvConfig` (`grammar_max_paragraphs`, `grammar_max_chars`, `grammar_max_errors`), the `[grammar]` keys of `analysis_settings.toml`, `CompleteTestSettings` and the settings tests; the README mentions, if any.
- Done when: the full suite passes in every commit, `ruff` is clean, no reference to the removed names remains in `src`, tests, TOML or README, and new behavior tests (grammar port receives abstract, title and every body paragraph, a very long body is not cut, adapter checks all paragraphs and returns more than ten errors, missing body raises) live in new test files.
