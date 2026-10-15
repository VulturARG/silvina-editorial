# Analysis Pipeline Baseline: Code vs LLM

- **Branch**: `silvina_editorial_v200`
- **Date**: 2026-10-15
- **Status**: Baseline of the current behavior. No source changes.
- **Related**: `odd/tasks/full-text-analysis-refactor-study.md`

## 1. Purpose

Record which parts of the document analysis are decided by deterministic code and which by an LLM, before studying the full-text refactor. This is the starting point for the inventory of text limits (TASK-01).

## 2. Summary

- The pipeline has **5 LLM calls** at most. Everything else is deterministic code.
- Only three domain services call `LlmGeneratorPort.generate`: `ArticleClassifier`, `QualityAnalyzer` and `EditorialSuitabilityAnalyzer` (verified with a search over `src/`).
- The LLM never decides the publication verdict directly, but the quality scores it produces are compared against thresholds in `PublicationVerdictEvaluator`.

## 3. Pipeline stages

Source: `AnalyzeDocumentUseCase._run_pipeline` (`src/application/analyze_document_use_case.py`).

| Stage | Method | Implementation |
| --- | --- | --- |
| `EXTRACT_CONTENT` | Code | Reads the docx: paragraphs, title, references, word count. Character count uses Word through COM (`Win32ComWordCountAdapter`). |
| `EXTRACT_CITATIONS` | Code | `DocxCitationAdapter`, `DocxReferenceAdapter`. |
| `VALIDATE_APA` | Code | `ApaValidator`. |
| `CHECK_GRAMMAR` | Code (no LLM) | LanguageTool (`language_tool_python`). The score comes from the error count (`GrammarScoreLevel.from_error_count`). |
| `CLASSIFY_ARTICLE` | Mixed | See section 4. |
| `ANALYZE_QUALITY` | LLM | See section 5. |
| `VALIDATE_STRUCTURE` | Code | `StructureValidator`: short headers matched against `structure_norms` aliases and compared with the sections required for the article type. |
| `MATCH_CITATIONS` | Code | `CitationMatcher`. |
| `INSPECT_FORMAT` | Code | `DocxEumicAdapter` (margins, fonts, and similar). |
| `BUILD_RECOMMENDATIONS` | Code | Rule classes and `PublicationVerdictEvaluator` (threshold comparisons). |

Stages marked "Code" were identified by their dependencies (none receives an LLM generator). `DocxCitationAdapter`, `ApaValidator` and `DocxEumicAdapter` internals were not read in detail.

## 4. Classification (0 or 1 LLM call)

Source: `src/domain/classification/article_classifier.py`.

Deterministic:

- Article size from the character count (`ArticleSizeClassifier`).
- IMRyD detector: keywords in paragraphs of at most 5 words (`ImrydSignalDetector`).
- Methodological vocabulary, signal S3 (`MethodologicalVocabularyDetector`).
- Reference count, signal S2a, 12 or more (`ReferenceSignalDetector`).
- Reference recency, signal S2b, by year regex (`ReferenceSignalDetector`).
- Rule table that combines the signals into an article type (`ClassificationRuleTable`).

LLM:

- Signals S4 (research intent), S5 (conclusive contribution) and S6 (theoretical justification).
- Prompt: `src/infrastructure/resources/prompts/classification/s4_s5_s6_signal_prompt.txt`.
- The model answers three lines (`S4: SI|NO`); `ArticleClassificationResponseParser` reads them.

Shortcut: if IMRyD is complete and the article size is in range, the result is `SCIENTIFIC` with confidence `IMRYD_OVERRIDE` and **no LLM call is made**.

## 5. Quality and editorial suitability (4 LLM calls)

Sources: `src/domain/quality/quality_analyzer.py`, `src/domain/quality/editorial_suitability_analyzer.py`.

| Call | Prompt | Output |
| --- | --- | --- |
| 1 | `clarity_coherence_prompt.txt` | Clarity and Coherence scores with feedback |
| 2 | `argumentation_conclusions_prompt.txt` | Argumentation and Conclusions scores with feedback |
| 3 | `contribution_prompt.txt` | Contribution verdict |
| 4 | `alignment_prompt.txt` (+ `research_lines.txt`) | Alignment verdict and matching lines |

Deterministic around the calls:

- Text sample construction (`QualityTextSampler`), shared by the four calls.
- Response parsing (`QualityResponseParser`, `EditorialSuitabilityParser` and their collaborators).
- Overall score: plain average of the four dimension scores.
- Quality level: `QualityLevel.from_score`.

## 6. Number of LLM calls per analysis

| Case | Calls |
| --- | --- |
| IMRyD complete (classification shortcut) | 4 |
| Otherwise | 5 |

## 7. Impact on the full-text refactor

- LLM calls receive a text built by samplers with configurable limits. Deterministic stages (APA, structure, references, format) already receive the whole document.
- Limits therefore matter only for the LLM calls and for grammar (see the inventory in the next document).
- Quality scores produced by the LLM feed the publication verdict, so a degraded LLM input or a silent placeholder score can change the verdict.
