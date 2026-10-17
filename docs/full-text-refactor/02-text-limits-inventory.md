# Inventory of Text Limits and Sampling Paths (TASK-01)

- **Branch**: `silvina_editorial_v200`
- **Date**: 2026-10-15
- **Status**: Read-only inventory of the current behavior. No source changes.
- **Related**: `odd/tasks/full-text-analysis-refactor-study.md`, `docs/full-text-refactor/01-pipeline-baseline.md`
- **Method**: exploration of the settings chain (TOML or `.env` key, `EnvConfig` attribute, wiring, consumer). The sampler and grammar adapter code was re-read to confirm the main findings. `.env.example` could not be read by the exploration tool, so `OLLAMA_NUM_CTX` was taken from a text search.

## 1. Limits that decide how much text reaches a stage

Values are the ones in `analysis_settings.toml` and `.env` at the time of writing.

| Limit | Key | Value | Consumer | Unit | Stage |
| --- | --- | --- | --- | --- | --- |
| Classification introduction | `[article_classification].sample_introduction_character_limit` | 75000 | `ArticleClassificationTextSampler.build_sample` | characters | LLM 1 |
| Classification ending | `[article_classification].sample_conclusion_character_limit` | 2500 | same | characters | LLM 1 |
| Classification fallback | `[article_classification].sample_fallback_character_limit` | 6000 | same | characters | LLM 1 |
| Bibliography header length | `[article_classification].bibliography_header_max_length` | 30 | `_strip_bibliography` | characters | LLM 1 |
| Quality sample limit | `[quality_text_sample].character_limit` | 75000 | `QualityTextSampler._join_to_paragraph_boundary` | characters, cut at paragraph end | LLM 2 to 5 |
| Minimum words of the sample | `[quality].min_sample_word_count` | 10000 | `QualityTextSampler.build_sample` | words, fallback switch | LLM 2 to 5 |
| Introduction paragraphs | `[quality_text_sample].introduction_paragraph_count` | 3 | same | paragraphs | LLM 2 to 5, strategic path |
| Middle paragraphs | `[quality_text_sample].middle_paragraph_count` | 2 | same | paragraphs | LLM 2 to 5, strategic path |
| Conclusion paragraphs | `[quality_text_sample].conclusion_paragraph_limit` | 3 | `_collect_conclusion_or_tail_paragraphs` | paragraphs | LLM 2 to 5, strategic path |
| Tail paragraphs | `[quality_text_sample].fallback_tail_paragraph_count` | 2 | same | paragraphs | LLM 2 to 5, strategic path |
| Conclusion marker | `[quality_text_sample].conclusion_header_marker` | `conclusi` | same | substring | LLM 2 to 5, strategic path |
| Reference line prefix | `[quality_text_sample].reference_line_prefix_length` | 80 | `_is_reference_like` | characters inspected | LLM 2 to 5, strategic path |
| Grammar paragraphs | `[grammar].max_paragraphs` | 20 | `LanguageToolAdapter._build_sample_text` | first N paragraphs | grammar |
| Grammar characters | `[grammar].max_chars` | 75000 | same | characters, hard cut | grammar |
| Grammar errors | `[grammar].max_errors` | 10 | `LanguageToolAdapter.check` | errors returned | grammar |
| Grammar suggestions | `[grammar].max_replacements` | 3 | `LanguageToolAdapter._map_to_dto` | suggestions per error | grammar |
| Article size thresholds | `[article_size].*` | 16000 to 40000 | `ArticleSizeClassifier.classify` | characters (Word COM count) | decides `OUT_OF_RANGE` and the IMRyD shortcut; does not cut text |
| Upload size | `[upload].max_size_bytes` | 26214400 | `validate_and_persist` | bytes | web API only |
| Ollama context | `OLLAMA_NUM_CTX` | 24576 | `OllamaGeneratorAdapter`, `OllamaLanguageModelWarmupAdapter` | tokens | the 5 LLM calls, Ollama only |
| Output budget and temperature | `[article_classifier].num_predict`, `temperature` | 300, 0.1 | `ArticleClassifier`, `EditorialSuitabilityAnalyzer` | output tokens | LLM 1, 4, 5 |
| Suitability output cuts | hard-coded in the use case wiring | 120, 120, 200, 120 | `EditorialSuitabilityParser`, `ContributionObservationBuilder` | characters of LLM output | LLM 4, 5 |
| Feedback items per section | hard-coded in `feedback_section_capper.py` | 8 | `FeedbackSectionCapper` | items of LLM output | LLM 2, 3 |

Report limits (`[report]`: 5 errors displayed, 150 characters of context) shape the output only and do not affect the input text.

## 2. Text built for each LLM call

### LLM 1: classification signals (S4, S5, S6)

Code: `ArticleClassifier.classify`, `ArticleClassificationTextSampler.build_sample`.

1. No paragraphs raises `ClassificationFailed`.
2. If IMRyD is complete and the size is in range, the classifier returns without calling the LLM.
3. The full text is the paragraphs joined with a space.
4. `_strip_bibliography` finds the first paragraph of at most 30 characters that contains one of `referencias`, `bibliografía`, `bibliography`, `fuentes bibliográficas` and cuts the text there.
5. Introduction: the first 75000 characters of the clean text.
6. Ending: the last 2500 characters, only when the clean text is longer than 75000.
7. The prompt receives the title separately and the sample.

With the current values a document without bibliography up to 75000 characters is sent whole. Above that, the cut falls in the middle of a word and the ending can overlap the introduction.

### LLM 2 and 3: clarity and coherence, argumentation and conclusions

Code: `QualityAnalyzer.analyze`, `QualityTextSampler.build_sample`. Both calls share one sample and send no generation options (no `num_predict`, no temperature).

1. Strategic path: title, first 3 paragraphs, 2 paragraphs from the middle, and a conclusion block.
2. Conclusion block: from the first paragraph that contains `conclusi` anywhere in its text, the paragraphs that are not reference-like, keeping the first 3. Without that marker, the last 2 non-reference paragraphs.
3. The parts are joined and cut after the paragraph that reaches 75000 characters.
4. If that sample has fewer than 10000 words, which is almost always the case because the strategic path is about 8 paragraphs, the sampler discards it and joins `document.paragraphs`, cut after the paragraph that reaches 75000 characters.

Effective behavior today: the quality prompts receive the whole document **including the bibliography and without the title**, up to roughly 75000 characters.

### LLM 4 and 5: contribution and alignment

Code: `EditorialSuitabilityAnalyzer.analyze`. They receive the same sample as LLM 2 and 3, unchanged, with `num_predict=300` and temperature 0.1. Alignment adds the research lines from `research_lines.txt`.

## 3. Bibliography stripping: three different rules

| Place | Rule | Used by |
| --- | --- | --- |
| `ArticleClassificationTextSampler._strip_bibliography` | first paragraph of at most 30 characters containing one of 4 lowercase markers; cuts everything after | classification sample only |
| `QualityTextSampler._is_reference_like` | the first 80 characters of a paragraph contain `http`, `https`, `doi.org` or `ISBN` | only inside the conclusion or tail block of the strategic path |
| `DocxReferenceAdapter._BIB_SECTION_PATTERN` | regex over the paragraphs concatenated without a separator, a marker followed by at least 100 characters; first occurrence anywhere | extracts `DocumentContentDTO.references`, not the body |

Not stripped: the quality fallback (the effective path), `MethodologicalVocabularyDetector` (joins all paragraphs), `ImrydSignalDetector` (only short headers) and grammar (first 20 paragraphs).

## 4. Hard-coded values and dead settings

Hard-coded (not configurable):

- Suitability output cuts 120, 120, 200, 120 and the cap of 8 feedback items per section.
- `_BIBLIOGRAPHY_MARKERS` and `ReferenceLineMarker`.
- IMRyD header candidates of at most 5 words.
- `MethodologicalVocabularyDetector` thresholds (4 terms, 1 hard term) and `ReferenceSignalDetector` thresholds (12 references, 4 years, 0.5 ratio).
- Title, author and abstract heuristics in `ParagraphContentAdapter` (first 5 paragraphs, fewer than 200 characters, first 15 for authors, more than 300 words for the abstract).
- Upload chunk size of 65536 bytes.

Without effect or nearly so:

- `sample_fallback_character_limit` (6000): the sample is empty only when there are no paragraphs, and `classify` already raised before that.
- The strategic path settings of the quality sampler (paragraph counts, marker, prefix length), because the 10000-word switch almost always selects the fallback.
- The `prompts/v2/` variants: the wiring loads only the v1 prompts.

## 5. Findings

1. **The study document is out of date.** It cites `character_limit = 32000` and `[grammar].max_chars = 5000`. Both are now 75000. The 65.8 % measurement was made with the old values.
2. **Grammar does not scale with the document.** `max_paragraphs = 20` is the limit that applies. Raising `max_chars` changes nothing unless those 20 paragraphs exceed it.
3. **Three notions of "bibliography"** with different markers and scope (section 3).
4. **Quality reads the bibliography, classification does not.** For documents under about 75000 characters LLM 2 to 5 receive it. This was estimated at about 40 % of the quality prompt tokens in a previous measurement.
5. **The `conclusi` marker matches anywhere in a paragraph.** A body paragraph that mentions "conclusión" starts the conclusion block early. This only matters on the strategic path, which is rarely used.
6. **Two measures of size.** `char_count` comes from Word through COM and decides the size and the IMRyD shortcut. Sampling limits use `len()` over the paragraphs read by python-docx.
7. **Tables, text boxes and footers are invisible to every stage.** `DocxTextAdapter` reads only body paragraphs and drops empty ones.
   Update: tables are now read by `DocxTableAdapter` and sent to the classification, quality and editorial suitability prompts as Markdown (`include-tables-in-prompt`). They still do not count toward `char_count`. Text boxes, footers and images remain invisible: for images only the figure captions reach the prompts.
8. **Generation options are asymmetric.** LLM 2 and 3 send none. LLM 4 and 5 reuse the `[article_classifier]` settings, which is a misleading name. `ClaudeGeneratorAdapter` ignores the options it receives, so `num_predict` and temperature apply to Ollama only.
9. **No guard ties the character limits to the context window.** 75000 characters is about 19 to 20 thousand tokens at the ratio measured earlier, close to `OLLAMA_NUM_CTX = 24576` once prompt and output are added. Ollama's behavior when a prompt exceeds the context was not verified in this inventory.
10. **Output of the LLM is cut again after parsing**: the first sentence and the 120 and 200 character limits in suitability, and the 8-item cap in feedback.

## 6. Not verified

- `FeedbackSectionCapState`, `QualityResponseParser` and the full v1 prompts were not read.
- `.env.example` was not read directly.
- Ollama truncation behavior for oversized prompts (point 9) is general knowledge, not observed here.

## 7. Questions this inventory answers for the study

- **Question 1** (limits per concern): answered in sections 1 and 4.
- **Question 4** (where "body without bibliography" should live): the three current rules are in section 3.
- **Questions 2, 3, 5, 6 and 7** need TASK-02 to TASK-04.
