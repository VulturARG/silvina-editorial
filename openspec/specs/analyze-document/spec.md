# Specification: Document Analysis Orchestrator & Recommendations (Slice 13 + Refactor)

> Normative guide: `.agent/skills/clean-architecture/SKILL.md`
> Parent proposal: `openspec/changes/analyze-document-orchestrator/proposal.md`
> Migration plan reference: `docs/plan-migracion-hexagonal.md`
> **Refactor note**: Slice 14 integration observations caused intentional divergences from the original Slice 13 spec. This document reflects the final implemented state.

---

## Purpose

This specification defines the behavior of the document analysis pipeline orchestrator, the domain service that generates editorial recommendations, and the supporting DTOs and configuration settings in compliance with clean hexagonal architecture guidelines.

---

## Requirements

### Requirement: RecommendationPriority Enum (3 members)

The `RecommendationPriority` enum MUST live in `src/domain/enums/recommendation_priority.py` and carry exactly **three** values representing severity levels for specific editorial recommendations:

- `HIGH` maps to `"alta"`
- `MEDIUM` maps to `"media"`
- `LOW` maps to `"baja"`

> **Rationale**: `CRITICAL`, `WARNING`, and `APPROVED` were removed from this enum because they represent a *publication verdict* — a semantically distinct concept. They live in `PublicationVerdict` (see below).

#### Scenario: RecommendationPriority contains exactly three members

- GIVEN the `RecommendationPriority` enum
- WHEN the list of members is queried
- THEN it has exactly 3 members: `HIGH`, `MEDIUM`, and `LOW`

#### Scenario: RecommendationPriority values match Spanish strings

- GIVEN the `RecommendationPriority` members
- WHEN their values are read
- THEN the values map to `"alta"`, `"media"`, and `"baja"` respectively

---

### Requirement: PublicationVerdict Enum

`PublicationVerdict` MUST live in `src/domain/enums/publication_verdict.py` and carry exactly **three** values representing the final editorial verdict for a document:

- `CRITICAL` maps to `"critica"`
- `WARNING` maps to `"advertencia"`
- `APPROVED` maps to `"aprobado"`

#### Scenario: PublicationVerdict contains exactly three members

- GIVEN the `PublicationVerdict` enum
- WHEN the list of members is queried
- THEN it has exactly 3 members: `CRITICAL`, `WARNING`, and `APPROVED`

---

### Requirement: PublicationVerdictDTO

`PublicationVerdictDTO` MUST be a frozen data transfer object inheriting from `BaseDTO` in `src/domain/dtos/publication_verdict_dto.py` with fields:
- `verdict: PublicationVerdict`
- `message: str`

#### Scenario: PublicationVerdictDTO is immutable

- GIVEN a constructed `PublicationVerdictDTO`
- WHEN any field is modified or reassigned
- THEN Python raises `FrozenInstanceError`

---

### Requirement: Immutable RecommendationDTO

`RecommendationDTO` MUST be a frozen data transfer object inheriting from `BaseDTO` in `src/domain/dtos/recommendation_dto.py` with fields:
- `priority: RecommendationPriority`
- `message: str`

#### Scenario: RecommendationDTO is immutable

- GIVEN a constructed `RecommendationDTO`
- WHEN any field is modified or reassigned
- THEN Python raises `FrozenInstanceError`

---

### Requirement: ClassificationResultDTO IMRyD Override Property

`ClassificationResultDTO` (in `src/domain/dtos/classification_result_dto.py`) MUST expose a read-only property `effective_structure_type: ArticleType` using guard clauses:

1. If `article_type` is NOT `ArticleType.CIENTIFICO`, return `article_type` immediately.
2. If `"IMRyD"` is in `(self.reasoning or "")` (case-sensitive), return `ArticleType.CIENTIFICO`.
3. Otherwise return `ArticleType.DIVULGACION`.

#### Scenario: Scientific article with IMRyD reasoning

- GIVEN a `ClassificationResultDTO` with `article_type = ArticleType.CIENTIFICO` and `reasoning` containing `"IMRyD"`
- WHEN `effective_structure_type` is called
- THEN it returns `ArticleType.CIENTIFICO`

#### Scenario: Scientific article without IMRyD reasoning

- GIVEN a `ClassificationResultDTO` with `article_type = ArticleType.CIENTIFICO` and `reasoning` not containing `"IMRyD"`
- WHEN `effective_structure_type` is called
- THEN it returns `ArticleType.DIVULGACION`

#### Scenario: Non-scientific article type

- GIVEN a `ClassificationResultDTO` with `article_type = ArticleType.DIVULGACION`
- WHEN `effective_structure_type` is called
- THEN it returns `ArticleType.DIVULGACION` unchanged

---

### Requirement: RecommendationSettingsDTO DTO (no defaults)

`RecommendationSettingsDTO` MUST be a frozen DTO inheriting from `BaseDTO` in `src/domain/dtos/recommendation_settings_dto.py`. All fields are **required** (no default values). Default values are the responsibility of the infrastructure config layer (`EnvConfig`):

- `publish_threshold: float`
- `quality_threshold: float`
- `grammar_threshold: float`
- `dimension_threshold: float`
- `citation_match_threshold: float`
- `critical_citation_match_threshold: float`
- `citation_count_threshold: int`
- `classification_confidence_threshold: float`
- `critical_quality_threshold: float`
- `critical_grammar_threshold: float`

> **Rationale**: Defaults in domain DTOs introduce hidden dependencies on infrastructure decisions. Defaults belong in `EnvConfig` (infrastructure config layer) and are resolved at wiring time.

---

### Requirement: EnvConfig Infrastructure Config Class

`EnvConfig` MUST reside in `src/infrastructure/env_config.py`. It MUST parse environment variables at instantiation, cast them, and cache them as typed instance attributes. Values for `APP_MODE` are `DEBUG` or `PROD` (case-insensitive); any other value fails fast. `METRICS_DATABASE_PATH` and `LOG_FILE_PATH` have no default and MUST be set; a missing or empty value fails fast naming the variable. `OLLAMA_THINK` accepts only `true` or `false` (case-insensitive) and any other value fails fast. It MUST expose a method `get_recommendation_settings() -> RecommendationSettingsDTO` to build recommendation settings.

The application version attribute (`silvina_version`) MUST be resolved dynamically:
- In production/standard mode: `EnvConfig` MUST load the version string from the file `version.txt` located in the project root directory (resolved relative to `EnvConfig` file location: `Path(__file__).resolve().parents[2] / "version.txt"`). The version string MUST be stripped of surrounding whitespace. If the file is missing or unreadable, `EnvConfig` MUST raise `FileNotFoundError` (or standard OS/permission errors).
- In testing mode (when the environment variable `TESTING` is `"True"`, `"true"`, or `"1"`): `EnvConfig` MUST fall back to loading the version from the environment variable `SILVINA_VERSION` (defaulting to `"0.9"` if the variable is not set), without requiring the `version.txt` file to exist.

| Env var | Type | Default | Attribute |
|---|---|---|---|
| `CITATION_MAX_AUTHOR_NAME_LENGTH` | `int` | `100` | `citation_max_author_name_length` |
| `GRAMMAR_MAX_REPLACEMENTS` | `int` | `3` | `grammar_max_replacements` |
| `STRUCTURE_MAX_HEADER_LENGTH` | `int` | `100` | `structure_max_header_length` |
| `ARTICLE_CLASSIFIER_TEMPERATURE` | `float` | `0.1` | `article_classifier_temperature` |
| `ARTICLE_CLASSIFIER_NUM_PREDICT` | `int` | `300` | `article_classifier_num_predict` |
| `ARTICLE_SIZE_SHORT_MIN_CHARS` | `int` | `16000` | `article_size_short_min_chars` |
| `ARTICLE_SIZE_SHORT_MAX_CHARS` | `int` | `24000` | `article_size_short_max_chars` |
| `ARTICLE_SIZE_UNDEFINED_MIN_CHARS` | `int` | `24001` | `article_size_undefined_min_chars` |
| `ARTICLE_SIZE_UNDEFINED_MAX_CHARS` | `int` | `35999` | `article_size_undefined_max_chars` |
| `ARTICLE_SIZE_LONG_MIN_CHARS` | `int` | `36000` | `article_size_long_min_chars` |
| `ARTICLE_SIZE_LONG_MAX_CHARS` | `int` | `40000` | `article_size_long_max_chars` |
| `QUALITY_LEVEL_EXCELLENT_THRESHOLD` | `float` | `9.0` | `quality_level_excellent_threshold` |
| `QUALITY_LEVEL_GOOD_THRESHOLD` | `float` | `7.0` | `quality_level_good_threshold` |
| `QUALITY_LEVEL_ACCEPTABLE_THRESHOLD` | `float` | `5.0` | `quality_level_acceptable_threshold` |
| `QUALITY_LEVEL_NEEDS_IMPROVEMENT_THRESHOLD` | `float` | `3.0` | `quality_level_needs_improvement_threshold` |
| `QUALITY_MIN_SAMPLE_WORD_COUNT` | `int` | `400` | `quality_min_sample_word_count` |
| `QUALITY_TEXT_SAMPLE_CHARACTER_LIMIT` | `int` | `8000` | `quality_text_sample_character_limit` |
| `OLLAMA_MODEL_NAME` | `str` | `"gemma4-26b-adapted"` | `ollama_model_name` |
| `OLLAMA_BASE_URL` | `str` | `"http://localhost:11434"` | `ollama_base_url` |
| `OLLAMA_THINK` | `bool` | `false` | `ollama_think` |
| `APP_MODE` | `AppMode` | `"PROD"` | `app_mode` |
| `METRICS_DATABASE_PATH` | `str` | `— (required)` | `metrics_database_path` |
| `LOG_FILE_PATH` | `str` | `— (required)` | `log_file_path` |
| `LOG_LEVEL` | `str` | `"INFO"` | `log_level` |
| `LOG_RETENTION_DAYS` | `int` | `14` | `log_retention_days` |
| `PUBLISH_THRESHOLD` | `float` | `7.0` | `publish_threshold` |
| `QUALITY_THRESHOLD` | `float` | `7.0` | `quality_threshold` |
| `GRAMMAR_THRESHOLD` | `float` | `7.0` | `grammar_threshold` |
| `DIMENSION_THRESHOLD` | `float` | `6.0` | `dimension_threshold` |
| `CITATION_MATCH_THRESHOLD` | `float` | `90.0` | `citation_match_threshold` |
| `CRITICAL_CITATION_MATCH_THRESHOLD` | `float` | `50.0` | `critical_citation_match_threshold` |
| `CITATION_COUNT_THRESHOLD` | `int` | `10` | `citation_count_threshold` |
| `CLASSIFICATION_CONFIDENCE_THRESHOLD` | `float` | `0.7` | `classification_confidence_threshold` |
| `CRITICAL_QUALITY_THRESHOLD` | `float` | `5.0` | `critical_quality_threshold` |
| `CRITICAL_GRAMMAR_THRESHOLD` | `float` | `5.0` | `critical_grammar_threshold` |
| `SILVINA_APP_NAME` | `str` | `"Silvina Editorial Assistant"` | `silvina_app_name` |
| `REPORT_SCORE_HIGH_THRESHOLD` | `float` | `8.0` | `report_score_high_threshold` |
| `REPORT_SCORE_MEDIUM_THRESHOLD` | `float` | `6.0` | `report_score_medium_threshold` |
| `REPORT_WORDS_PER_PAGE` | `int` | `250` | `report_words_per_page` |
| `REPORT_MAX_ERRORS_DISPLAYED` | `int` | `5` | `report_max_errors_displayed` |
| `REPORT_CONTEXT_TRUNCATION_LIMIT` | `int` | `150` | `report_context_truncation_limit` |
| `REPORT_MAX_REPLACEMENTS` | `int` | `3` | `report_max_replacements` |

> **Naming note**: the `PUBLISH_THRESHOLD` … `CRITICAL_GRAMMAR_THRESHOLD` variables (recommendation thresholds) carry no `RECOMMENDATION_` prefix. In `.env`/`.env.example` they MUST be grouped under a section comment (e.g. `# Recommendation thresholds`) instead of relying on a name prefix for grouping.

#### Scenario: EnvConfig defaults are loaded when env is empty and version.txt exists

- GIVEN an empty environment except for a valid `version.txt` file with content `"1.2.3"`
- WHEN `EnvConfig` is instantiated
- THEN attributes match the defaults in the table above
- AND `env_config.silvina_version` is `"1.2.3"`

#### Scenario: EnvConfig parses and casts environment variables

- GIVEN environment contains `CITATION_MAX_AUTHOR_NAME_LENGTH=150`
- AND a valid `version.txt` file exists
- WHEN `EnvConfig` is instantiated
- THEN `env_config.citation_max_author_name_length == 150`

#### Scenario: EnvConfig fails fast when version.txt is missing

- GIVEN the `version.txt` file is missing in the root directory
- AND `TESTING` environment variable is not set to `"True"`, `"true"`, or `"1"`
- WHEN `EnvConfig` is instantiated
- THEN a `FileNotFoundError` is raised

#### Scenario: EnvConfig falls back to environment variable in testing mode

- GIVEN `TESTING` environment variable is set to `"True"`
- AND `SILVINA_VERSION` environment variable is set to `"0.99"`
- AND `version.txt` is missing
- WHEN `EnvConfig` is instantiated
- THEN `env_config.silvina_version` is `"0.99"`

#### Scenario: EnvConfig uses testing default version when not specified in env

- GIVEN `TESTING` environment variable is set to `"True"`
- AND `SILVINA_VERSION` environment variable is not set
- AND `version.txt` is missing
- WHEN `EnvConfig` is instantiated
- THEN `env_config.silvina_version` is `"0.9"`

---

### Requirement: AnalysisContext Value Object

`AnalysisContext` MUST reside in `src/domain/recommendation/analysis_context.py` as a frozen dataclass grouping all analysis inputs and settings required by recommendation rules:

- `classification: ClassificationResultDTO`
- `quality: QualityResultDTO`
- `structure: StructureValidationResultDTO`
- `citations: CitationAnalysisResultDTO`
- `apa_validation: ApaValidationResultDTO`
- `grammar: GrammarCheckResultDTO`
- `settings: RecommendationSettingsDTO`

It MUST expose a computed property `citation_match_rate: float` returning `100.0` when `total_citations == 0`, otherwise `matched_count / total_citations * 100.0`.

---

### Requirement: RecommendationRule Abstract Base

`RecommendationRule` MUST reside in `src/domain/recommendation/recommendation_rule.py` as an abstract base class with a single abstract method:

```python
def evaluate(self, context: AnalysisContext) -> list[RecommendationDTO]: ...
```

---

### Requirement: Concrete Recommendation Rules

Seven concrete rule classes MUST reside in `src/domain/recommendation/`, one class per file, each implementing `RecommendationRule`:

1. **`QualityRule`** (`quality_rule.py`) — `HIGH` when `quality.overall_score < settings.quality_threshold`
2. **`GrammarRule`** (`grammar_rule.py`) — `HIGH` when `grammar.score < settings.grammar_threshold`
3. **`DimensionRule`** (`dimension_rule.py`) — `MEDIUM` for each dimension score below `settings.dimension_threshold`
4. **`StructureRule`** (`structure_rule.py`) — `HIGH` for each missing section when `structure.is_valid is False`
5. **`CitationMatchRule`** (`citation_match_rule.py`) — `HIGH` when match rate below `citation_match_threshold`; `MEDIUM` when unmatched count > 0 but above threshold
6. **`CitationCountRule`** (`citation_count_rule.py`) — `MEDIUM` when `total_citations < settings.citation_count_threshold`
7. **`ConfidenceRule`** (`confidence_rule.py`) — `LOW` when `classification.confidence` is not `None` and below `settings.classification_confidence_threshold`

---

### Requirement: PublicationVerdictEvaluator Domain Service

`PublicationVerdictEvaluator` MUST reside in `src/domain/recommendation/publication_verdict_evaluator.py`. Its method `evaluate(context: AnalysisContext) -> PublicationVerdictDTO` determines the final publication verdict:

- **`CRITICAL`** if any of: `quality < 5.0`, `grammar < 5.0`, `structure.is_valid is False`, `match_rate < critical_citation_match_threshold`, OR `total_citations == 0`
- **`WARNING`** if any of: `quality < publish_threshold`, `grammar < publish_threshold`, `match_rate < citation_match_threshold`, `len(apa_validation.violations) > 0`
- **`APPROVED`** otherwise

---

### Requirement: RecommendationBuilder Domain Service (Rule Pattern)

`RecommendationBuilder` MUST reside in `src/domain/recommendation/recommendation_builder.py`. Its constructor accepts:
- `settings: RecommendationSettingsDTO`
- `rules: list[RecommendationRule] | None` (defaults to the 7 concrete rules)
- `verdict_evaluator: PublicationVerdictEvaluator | None` (defaults to a new instance)

Its method `build(...) -> tuple[list[RecommendationDTO], PublicationVerdictDTO]` MUST:
1. Build an `AnalysisContext` from the inputs and settings.
2. Call `rule.evaluate(context)` for each rule and concatenate results.
3. Call `verdict_evaluator.evaluate(context)` to get the verdict.
4. Return `(recommendations, verdict)`.

> **Rationale**: The Rule pattern makes each recommendation rule independently testable and eliminates long `if/elif` chains. The verdict is a distinct return value (not a recommendation) to reflect its semantic difference.

#### Scenario: All thresholds satisfied — APPROVED verdict, empty recommendations

- GIVEN `RecommendationBuilder` with default rules and all analysis inputs satisfying thresholds
- WHEN `build()` is executed
- THEN it returns `([], PublicationVerdictDTO(verdict=PublicationVerdict.APPROVED, ...))`

#### Scenario: Quality below threshold — HIGH recommendation + WARNING verdict

- GIVEN a quality score of `6.5` (above critical but below `quality_threshold=7.0`)
- WHEN `build()` is executed
- THEN the list contains a `HIGH` recommendation for quality AND the verdict is `WARNING`

#### Scenario: Critical quality issue — CRITICAL verdict

- GIVEN a quality score of `4.5` (below critical threshold `5.0`)
- WHEN `build()` is executed
- THEN the verdict is `CRITICAL`

#### Scenario: Zero citations — CRITICAL verdict

- GIVEN `total_citations == 0`
- WHEN `build()` is executed
- THEN the verdict is `CRITICAL` with a message about missing APA citations

---

### Requirement: DocumentContentExtractor Domain Service

The `DocumentContentExtractor` domain service MUST reside in `src/domain/document/document_content_extractor.py`. It SHALL extract document content from a DOCX file using ports and handle count fallback logic.
- Constructor MUST inject: `document_text_port: DocumentTextPort`, `content_extraction_port: ContentExtractionPort`, and `character_count_port: CharacterCountPort`.
- Method `extract_content(docx_path: str) -> DocumentContentDTO`:
  1. Calls `document_text_port.read_paragraphs(path=docx_path)` to load paragraphs.
  2. Calls `content_extraction_port.extract(paragraphs, docx_path)` to get a base DTO.
  3. Calls `character_count_port.count(docx_path)`. On `CharacterCountUnavailable` or if result is `None`, returns the base DTO. Otherwise, returns a new DTO replacing word, char, and paragraph counts with the counted values.

#### Scenario: Content extraction executes successfully with count fallback
- GIVEN a valid DOCX path and `character_count_port` raises `CharacterCountUnavailable`
- WHEN `extract_content` is called
- THEN it returns a `DocumentContentDTO` containing text-based fallback counts

---

### Requirement: CitationExtractor Domain Service

The `CitationExtractor` domain service MUST reside in `src/domain/citation/citation_extractor.py`. It SHALL extract citations and references from a DOCX file.
- Constructor MUST inject: `citation_extraction_port: CitationExtractionPort` and `reference_extraction_port: ReferenceExtractionPort`.
- Method `extract_citations_and_references(docx_path: str) -> tuple[list[CitationDTO], list[ReferenceDTO], str]`:
  1. Calls `citation_extraction_port.extract_citations(docx_path=docx_path)`.
  2. Calls `reference_extraction_port.extract_references(docx_path=docx_path)`.
  3. Returns the tuple `(citations, references, section_type)`.

#### Scenario: Citations and references are extracted
- GIVEN a valid DOCX path
- WHEN `extract_citations_and_references` is called
- THEN it returns a tuple of citations, references, and references section type

---

### Requirement: DocumentFormatInspector Domain Service

The `DocumentFormatInspector` domain service MUST reside in `src/domain/document/document_format_inspector.py`. It SHALL inspect formatting rules.
- Constructor MUST inject: `document_format_inspection_port: DocumentFormatInspectionPort`.
- Method `inspect(docx_path: str, word_count: int) -> list[EumicViolationDTO]`:
  1. Calls `document_format_inspection_port.inspect(docx_path=docx_path, word_count=word_count)`.

#### Scenario: Format inspection finds violations
- GIVEN a document path and word count
- WHEN `inspect` is called
- THEN it returns a list of formatting violations

---

### Requirement: GrammarChecker Domain Service

The `GrammarChecker` domain service MUST reside in `src/domain/grammar/grammar_checker.py`. It SHALL perform grammar checks and compute score level.
- Constructor MUST inject: `grammar_check_port: GrammarCheckPort`.
- Method `check_grammar(paragraphs: list[str]) -> GrammarCheckResultDTO`:
  1. Calls `grammar_check_port.check(paragraphs=paragraphs)`.
  2. Maps error count using `GrammarScoreLevel.from_error_count(error_count=len(errors))`.
  3. Returns `GrammarCheckResultDTO(score=level.score, feedback=level.feedback, errors=errors)`.

#### Scenario: Grammar check returns errors and level
- GIVEN a list of paragraphs
- WHEN `check_grammar` is called
- THEN it returns a `GrammarCheckResultDTO` with grammar score and feedback

---

### Requirement: AnalyzeDocumentUseCase Orchestrator

`AnalyzeDocumentUseCase` MUST live in `src/application/analyze_document_use_case.py` and coordinate the document analysis steps. It accepts its 10 domain service dependencies via constructor injection:
- Domain services: `document_content_extractor`, `citation_extractor`, `document_format_inspector`, `grammar_checker`, `apa_validator`, `article_classifier`, `quality_analyzer`, `structure_validator`, `citation_matcher`, `recommendation_builder`.
(Previously: Accepted 7 ports, 5 domain services, and 1 builder — 13 dependencies total.)

Method `execute(document_path: str, document_name: str | None = None) -> ReportInputDTO` MUST be wrapped with `@generic_error_handler` and perform:
When `document_name` is provided, it is used as the display name for analysis tracking and the returned `ReportInputDTO.filename`. When `document_name` is omitted or `None`, it falls back to `document_path`. The file-reading stages continue to use `document_path`.
1. Extract content via `document_content_extractor.extract_content(document_path)`.
2. Extract citations/references via `citation_extractor.extract_citations_and_references(document_path)`.
3. Validate APA citations via `apa_validator.validate_all_citations(citations, document_content.paragraphs)`.
4. Grammar check via `grammar_checker.check_grammar(document_content.paragraphs)`.
5. Classify article via `article_classifier.classify(document_content)`.
6. Analyze quality via `quality_analyzer.analyze(document_content)`.
7. Validate structure via `structure_validator.validate_structure(document_content, classification.effective_structure_type, len(references) > 0)`.
8. Parse references section type to `SectionName`, falling back to `REFERENCES` on `ValueError`.
9. Match citations via `citation_matcher.match_citations_to_references(citations, references, section_name)`.
10. Verify format/EUMIC via `document_format_inspector.inspect(document_path, document_content.word_count)`.
11. Call `recommendation_builder.build(...)` -> `(recommendations, verdict)`.
12. Return `ReportInputDTO`.

#### Scenario: Orchestrator executes all pipeline steps sequentially
- GIVEN a valid `document_path`
- WHEN `execute(document_path)` is called
- THEN each of the 10 domain service dependencies is invoked and a `ReportInputDTO` is returned

#### Scenario: Orchestrator uses custom document name for telemetry and report
- GIVEN a valid `document_path` and a custom `document_name`
- WHEN `execute(document_path, document_name)` is called
- THEN analysis tracking and the returned `ReportInputDTO` use `document_name` while extraction stages receive `document_path`

#### Scenario: Orchestrator falls back to document path when document name omitted
- GIVEN a valid `document_path` and `document_name` is None
- WHEN `execute(document_path)` is called
- THEN analysis tracking and the returned `ReportInputDTO` fall back to `document_path`

#### Scenario: Structure validation uses effective structure type
- GIVEN a scientific article without "IMRyD" in reasoning
- WHEN structure validation is invoked
- THEN the orchestrator calls `structure_validator.validate_structure` with `article_type=ArticleType.DIVULGACION`

---

### Requirement: AnalyzeDocumentUseCaseWiring Assembly Factory

`AnalyzeDocumentUseCaseWiring` MUST reside in `src/infrastructure/wirings/analyze_document_use_case_wiring.py`. It MUST follow the private-method wiring pattern where:
- `create_use_case()` instantiates `EnvConfig` and delegates dependency injection to `_get_xxx()` private methods, injecting the configurations from the `EnvConfig` instance.
- Port helper methods instantiate and memoize/return infrastructure adapters.
- Domain service helper methods build the 10 domain services directly, wrapping ports or LLM generator dependencies as required.
- `_get_document_content_extractor()` returns `DocumentContentExtractor(self._get_document_text_port(), self._get_content_extraction_port(), self._get_character_count_port())`.
- `_get_citation_extractor()` returns `CitationExtractor(self._get_citation_extraction_port(), self._get_reference_extraction_port())`.
- `_get_document_format_inspector()` returns `DocumentFormatInspector(self._get_document_format_inspection_port())`.
- `_get_grammar_checker()` returns `GrammarChecker(self._get_grammar_check_port())`.
(Previously: Constructed and injected 7 ports and 5 domain services directly into the orchestrator.)

#### Scenario: Wiring constructs correct dependency graph
- GIVEN the wiring configuration
- WHEN `AnalyzeDocumentUseCaseWiring().create_use_case()` is called
- THEN it returns a valid `AnalyzeDocumentUseCase` with all 10 domain service dependencies injected

#### Scenario: Article classifier and quality analyzer share one LLM generator instance
- GIVEN `AnalyzeDocumentUseCaseWiring().create_use_case()`
- WHEN `result._article_classifier._llm_generator` and `result._quality_analyzer._llm_generator` are compared
- THEN they are the exact same object (`is`), not merely equal instances

#### Scenario: Environment variable overrides threshold at wiring time
- GIVEN `QUALITY_THRESHOLD=6.5` is set in the environment before `create_use_case()` instantiates `EnvConfig`
- WHEN `create_use_case()` is called
- THEN `recommendation_builder._settings.quality_threshold` equals `6.5`

---

### Requirement: Cooperative Analysis Cancellation

Analysis execution MUST support cooperative cancellation upon client disconnection to avoid occupying single-slot AI resources with orphan analyses.
- `AnalysisCancellationPort` (in `src/domain/metrics/analysis_cancellation_port.py`) defines the interface: `bind_new_cancellation_signal()`, `request_cancellation()`, `is_cancellation_requested()`, and `clear_cancellation_signal()`.
- `AnalysisCancellationAdapter` (in `src/infrastructure/adapters/metrics/analysis_cancellation_adapter.py`) manages context-local state using a class-level `ContextVar[threading.Event | None]`, ensuring signals are shared across instances and propagated to thread pool worker tasks.
- `AnalysisCancelled` (in `src/domain/exceptions/analysis_errors.py`) inherits from `SrcBaseWarning` with message `"The analysis was cancelled because the client disconnected."`.
- `ExecutionStatus` includes `CANCELLED = "cancelled"`.
- `AnalysisTracker.track_stage` checks `is_cancellation_requested()` before invoking the stage operation. If requested, it raises `AnalysisCancelled` immediately without executing the stage or recording stage latency.
- `AnalysisTracker.track_analysis` catches `AnalysisCancelled`, records completion telemetry with status `ExecutionStatus.CANCELLED`, logs an INFO message with elapsed milliseconds (not ERROR), re-raises `AnalysisCancelled`, and clears the cancellation signal in `finally`.
- The FastAPI upload endpoint `/analyze` runs as an asynchronous handler (`async def`), binds a fresh cancellation signal, executes analysis in a thread pool via `anyio.to_thread.run_sync`, concurrently watches for `http.disconnect` events via `request.receive()`, requests cancellation upon disconnect, and clears the signal in `finally`.

#### Scenario: Cancellation requested before stage boundary stops pipeline
- GIVEN an active analysis where cancellation has been requested via `AnalysisCancellationPort`
- WHEN `AnalysisTracker.track_stage` is invoked for a subsequent stage
- THEN it raises `AnalysisCancelled` before executing the stage
- AND no duration telemetry is recorded for the skipped stage

#### Scenario: Cancelled analysis records CANCELLED execution status and logs at INFO
- GIVEN an active analysis pipeline that raises `AnalysisCancelled`
- WHEN `AnalysisTracker.track_analysis` catches the exception
- THEN it records completion telemetry with status `ExecutionStatus.CANCELLED` and null metrics
- AND it emits an INFO log containing the elapsed time
- AND it re-raises `AnalysisCancelled` without emitting ERROR logs

#### Scenario: Pipeline completes successfully when no cancellation is requested
- GIVEN an active analysis where no cancellation signal is requested
- WHEN all pipeline stages execute to completion
- THEN completion telemetry is recorded with status `ExecutionStatus.SUCCESS`
- AND the cancellation signal is cleared upon exit
