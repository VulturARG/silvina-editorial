# Feature: Full-Text Body Refactor

- **Feature Name**: `full-text-body-refactor`
- **File Locator**: `odd/tasks/full-text-body-refactor.md`
- **Base branch**: `silvina_editorial_v200`; each task lives on its own branch from the base and is merged by pull request when the user orders it
- **Design**: `docs/full-text-refactor/04-design-options-and-task-plan.md` (decisions D1 to D7 approved by the user on 2026-10-15)
- **Commit policy**: stop before every commit and wait for the user's instructions. Commits by type in this order: `docs`, then code (`feat`, `refactor`, `chore` or `fix`), then `test`. The code commit includes the minimal adjustments to existing tests so that the full suite passes in every commit; the test commit holds only new behavior tests, preferably in new test files.
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

- [x] **TASK-01: Editorial norms for the body** (about 80 to 120 lines): `[bibliography]` (`header_markers`, `header_max_length`) and `[article_length]` (`max_body_chars`) in `editorial_norms.toml`, their DTOs, `EditorialNormsDTO`, `EditorialNormsLoader` with validation, test builder support. No consumer yet. Verified on branch `refactor/editorial-norms-for-body`: 2128 tests pass (baseline 2119 plus 9 new), ruff clean, 70 production code lines (cap 400), mutation check (dropping `.lower()` in the marker normalization) caught by 2 tests. Commits pending the user's order.
- [ ] **TASK-02: `ArticleBodyDTO` and `ArticleBodyLocator`** (about 130 to 170 lines): new files only, no consumer yet.
- [ ] **TASK-03: Body in `DocumentContentDTO` and the extractor** (about 60 to 100 lines): new `body` field, `DocumentContentExtractor` uses the locator, wiring; remove the old `abstract` field, `_extract_abstract` and their tests.
- [ ] **TASK-04: `EXTRA_LONG` size and size on the body** (about 70 to 110 lines): `ArticleSize.EXTRA_LONG`, thresholds, classifier and IMRyD gate use the body count; the upper end comes from the norms.
- [ ] **TASK-05: Maximum length check** (about 90 to 130 lines): domain service, Spanish exception, stage `VALIDATE_ARTICLE_LENGTH`, use case call, wiring.
- [ ] **TASK-06: Classification reads the body** (about 140 to 190 lines): remove `ArticleClassificationTextSampler`, its settings DTO, 4 `EnvConfig` attributes and TOML keys; wiring.
- [ ] **TASK-07: Quality and suitability read the body** (about 200 to 260 lines): remove `QualityTextSampler`, its settings DTO and 9 settings; wiring.
- [ ] **TASK-08: Grammar reads body plus abstract** (about 80 to 130 lines): remove `max_paragraphs`, `max_chars` and `max_errors`; wiring.

## 4. TASK-01 detail

- `editorial_norms.toml` gets:
  - `[bibliography]` with `header_markers = ["referencias", "bibliografía", "bibliography", "fuentes bibliográficas"]` and `header_max_length = 30`;
  - `[article_length]` with `max_body_chars = 75000`.
- New DTOs `BibliographyNormsDTO` and `ArticleLengthNormsDTO`; `EditorialNormsDTO` gets the fields `bibliography` and `article_length`.
- `EditorialNormsLoader` reads both sections, normalizes the markers (stripped, lowercase, without duplicates) and raises `EditorialNormInvalid` when `header_max_length` or `max_body_chars` is below 1.
- `build_editorial_norms_for_test` accepts overrides for the new fields.
- Done when: the real file loads into the complete DTO, the missing-section and invalid-value cases raise the existing error types, the full suite passes, and `ruff` is clean.
