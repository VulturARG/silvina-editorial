# Design Decisions and Task Plan (TASK-03)

- **Branch**: `silvina_editorial_v200`
- **Date**: 2026-10-15
- **Status**: All design decisions taken by the user on 2026-10-15. The task plan awaits the user's final approval (TASK-05). No source changes.
- **Related**: `docs/full-text-refactor/01-pipeline-baseline.md`, `02-text-limits-inventory.md`, `03-full-text-cost-measurement.md`, `odd/tasks/full-text-analysis-refactor-study.md`
- **Requirements source**: question and answer session with the user on 2026-10-15, saved in Engram under the topic `odd/full-text-analysis-refactor-study/requirements`.

## 1. Agreed requirements

| Area | Decision |
| --- | --- |
| Goal | Work with the whole document. Remove every limit on how much text each stage reads. Keep only one maximum size for the article. |
| Maximum | 75000 characters for the first tests; temporary and adjusted manually. Counted over the body (no bibliography, no abstract). Lives in `editorial_norms.toml`, not overridable by environment variables. The system does nothing else about the model context. |
| Rejection | Above the maximum nothing is analyzed. Same handling as a document over 25 MB (error message, no report). Message in Spanish. |
| Body | Starts at the repeated title (editorial rule: the title is repeated, bold and centered, right before the body; always present). Ends before the bibliography header. Everything before it is excluded (title on top, authors, affiliation, author note, funding, conflict of interest, correspondence, abstract, keywords). Tables do not count toward the body size and the maximum, but since the `include-tables-in-prompt` feature they are sent to the prompts as Markdown at their original position (see `odd/tasks/include-tables-in-prompt.md`). |
| Title | Only the repeated title at the start of the body is taken, and it is sent once. The title on top of the document is discarded with the header. |
| Abstract | Starts at the abstract heading. Not cut by any word or character count. Ends at the keywords list or at the repeated title. |
| Markers | No constants in the code. Abstract headings and keyword markers are read from `editorial_norms.toml` (`[abstract].section_keywords` and `[keywords].section_markers`, lists unchanged). Bibliography markers and header length go in a new `[bibliography]` section of `editorial_norms.toml`. |
| Bibliography | Keep the current text rule: a paragraph of at most 30 characters containing one of the markers (`referencias`, `bibliografía`, `bibliography`, `fuentes bibliográficas`). |
| Size ranges | Measured over the body. Below `long_max_chars` as today. Between `long_max_chars` and the maximum: extra long, processed, and behaves exactly like long (the IMRyD shortcut applies). |
| LLM input | The body, for all 5 calls. |
| Grammar | The same body plus the abstract. `max_paragraphs`, `max_chars` and `max_errors` are removed. Spelling is unchanged (misspellings stay discarded). |
| Unchanged | Deterministic stages (APA, citations, structure, IMRyD, vocabulary, format) keep reading the document as today. LLM output cuts (120, 200, 8 items, 3 replacements) are out of scope. |
| Process | Tasks of at most about 400 lines of changed code. Commits by type. No commit without the user's order. |

Still unknown to the user: whether the repeated title could differ from the first paragraph ("no sé"). The rules were derived from the 30 documents in `sandbox/pack_1` and `sandbox/pack_2` and will be adjusted later if needed.

## 2. Current and target flow

Current: each LLM call builds its own text with its own sampler and limits; grammar cuts the first 20 paragraphs; the size category uses the Word character count of the whole document.

Target:

1. `DocumentContentExtractor` reads the paragraphs as today and asks the new domain service `ArticleBodyLocator` to locate the abstract and the body, using markers from the editorial norms.
2. The result (`ArticleBodyDTO`) is stored in a new `DocumentContentDTO.body` field. `paragraphs`, `char_count`, `title` and the other fields stay, so every stage not mentioned above is untouched.
3. A new stage `VALIDATE_ARTICLE_LENGTH`, right after `EXTRACT_CONTENT`, rejects bodies above the maximum.
4. Classification, quality, suitability and grammar read the located body (and the abstract for grammar) instead of sampling.

The locator uses the first paragraph of the document only as a search key to find the repeated title; that paragraph is never the title that is sent. If a document breaks the editorial rule, the locator raises a plain domain error (implementation detail, to review in TASK-05).

## 3. Decisions taken

| Id | Question | Decision |
| --- | --- | --- |
| D1 | Where the body is located | New domain service `ArticleBodyLocator`, called by `DocumentContentExtractor`. |
| D2 | How the result is stored | New `ArticleBodyDTO` (title, abstract paragraphs, body paragraphs) in a new `DocumentContentDTO.body` field; `paragraphs` is not replaced. The old `DocumentContentDTO.abstract` field (cut at 300 words, no production reader) is removed together with `ParagraphContentAdapter._extract_abstract` and its tests. |
| D3 | Source of markers | `editorial_norms.toml`, no constants in code. Abstract and keyword lists unchanged. New `[bibliography]` section with `header_markers` and `header_max_length`; the value 30 leaves the code and the old key `[article_classification].bibliography_header_max_length` disappears with the classification sampler. |
| D4 | Missing repeated title | Closed by the user: it always exists. No fallback designed. |
| D5 | Where the length check lives | New domain service plus the new stage `VALIDATE_ARTICLE_LENGTH`; new exception in `document_errors.py` with a Spanish message. |
| D5b | Where the maximum is written | `editorial_norms.toml`, not overridable by environment variables. The other ranges stay in `analysis_settings.toml`; the upper end of "extra long" comes from the norms. |
| D6 | Title sent once | `ArticleBodyDTO` keeps the title apart from the paragraphs after it. Classification passes `{title}` plus the other paragraphs; quality and suitability pass title plus paragraphs as `{text_sample}`. Prompt files do not change. |
| D7 | The 400 lines | Added plus removed lines of `.py` files under `src/` that are not tests (`git diff --numstat`). `.toml` files, tests, `.md` and `odd/` are not counted. |
| Commits | Tension with docs, code, tests | Hybrid. The code commit includes the minimal adjustments to existing tests so that every commit passes the full suite (signatures, constructors, deletion of tests of removed code). The test commit holds only new behavior tests. Tasks that only add code are unaffected. |

The web handler already turns any `BaseSrcError` into an error box (status 400) and the CLI prints it as text, so the rejection needs no new delivery code. Message wording still to be refined with the user. A starting text: "Artículo rechazado: el cuerpo supera el máximo de N caracteres permitido por la editorial."

## 4. Task plan (estimates, not measurements)

| Task | Content | Estimated code lines |
| --- | --- | --- |
| 1 | Editorial norms for the body: `[bibliography]` and the maximum in `editorial_norms.toml`, their DTOs and the loader. | 80 to 120 |
| 2 | `ArticleBodyDTO` and `ArticleBodyLocator`, new files only, no consumer yet. | 130 to 170 |
| 3 | `DocumentContentDTO.body`, `DocumentContentExtractor` uses the locator, wiring; removal of the old `abstract` field and `_extract_abstract`. | 60 to 100 |
| 4 | `ArticleSize.EXTRA_LONG`; the size classifier and the IMRyD gate use the body character count; the extra-long upper end comes from the norms. | 70 to 110 |
| 5 | Length check: domain service, new exception (Spanish message), new stage, use case call, wiring. | 90 to 130 |
| 6 | Classification reads the body: remove `ArticleClassificationTextSampler`, its settings DTO, 4 `EnvConfig` attributes and TOML keys, wiring. | 140 to 190 |
| 7 | Quality and suitability read the body: remove `QualityTextSampler`, its settings DTO, 9 settings (`min_sample_word_count` and `[quality_text_sample]`), wiring. | 200 to 260 |
| 8 | Grammar reads body plus abstract: remove `max_paragraphs`, `max_chars` and `max_errors` from the adapter, settings, `EnvConfig`, TOML and wiring. | 80 to 130 |

Order: 1 to 5 add behavior without changing what the LLM receives (task 4 changes the size category of some documents, see risks). Then 6, 7, 8 switch each consumer and may go in any order. The total is about 850 to 1210 lines of code over 8 tasks, each under 400. Documentation goes in each task's docs commit.

## 5. Risks

- **Rules derived from 30 samples.** The repeated-title rule and the markers may fail on real documents; the locator raises an error instead of guessing.
- **Size categories shift.** Measured over the body, 6 of the 30 samples change category (for example `03_IMRyD_Vargas_Prado` goes from "no definido" to "corto"). None exceeds 75000 characters.
- **Scores may shift.** The quality prompts and thresholds were tuned on excerpts. The earlier comparison (Engram, 2026-10-05) showed higher scores with the full text.
- **Cost.** About 40 to 50 percent more prompt tokens per analysis (document 03). Latency was not measured (controlled run skipped by the user).
- **Context.** The system does not check that the body fits `OLLAMA_NUM_CTX`; the user adjusts the maximum by hand.
- **Tests that read the settings files.** Settings keys are removed, so `CompleteTestSettings`, the mapping test of `EnvConfig`, the editorial norms builder and the wiring tests need updates.
- **Format inspection.** The abstract and keyword lists are shared with `DocxEumicAdapter` and stay unchanged, so its behavior does not change.

## 6. TASK-04 note

The parser robustness proposal of the study (header tolerance and failing on a missing dimension) was already delivered in PR #84: the header accepts `#{1,6} N. <dimension>` and `QualityAnalyzer` requires both dimensions of each call. It is not part of this plan.
