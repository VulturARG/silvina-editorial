# LLM-Backed Quality Analysis Specification

## Purpose

LLM-mediated document quality scoring across 4 semantic dimensions (Claridad,
Coherencia, Argumentación, Conclusiones), produced via two sequential prompts to a
text-generation backend reached only through a port. First capability in the
migration with an external dependency — establishes the port/adapter pattern and
naming convention reused by future LLM-calling slices.

## Requirements

### Requirement: LlmGeneratorPort Contract

`LlmGeneratorPort` (`src/domain/ports/llm_generator_port.py`) MUST be an abstract
interface declaring exactly one method, `generate(prompt: str) -> str`. The
signature MUST contain no Ollama-specific types, parameters, or return shapes —
only a plain string in, plain string out.

#### Scenario: Port has no vendor-specific leakage

- GIVEN the `LlmGeneratorPort` interface definition
- WHEN its method signatures are inspected
- THEN the only method is `generate(prompt: str) -> str` and no parameter or
  return type references Ollama or any other concrete vendor

### Requirement: OllamaGeneratorAdapter Implements the Port

`OllamaGeneratorAdapter` (`src/infrastructure/adapters/llm_generator/ollama_generator_adapter.py`)
MUST implement `LlmGeneratorPort`, wrapping a real call to `ollama.generate()`.
It MUST be the only file in the slice that imports `ollama`. On success, it MUST
extract and return `response.get('response', '').strip()` from Ollama's response
dict — the domain layer MUST never see that raw dict shape. Its `generate` method
MUST be decorated with `@generic_error_handler`.

#### Scenario: Successful generation returns the stripped response text

- GIVEN a working Ollama backend that returns `{'response': '  some text  '}`
- WHEN `OllamaGeneratorAdapter.generate(prompt)` is called
- THEN it returns `"some text"` as a plain string

#### Scenario: Backend failure raises LanguageModelUnavailable

- GIVEN the underlying `ollama.generate()` call raises a connection error, timeout,
  or any backend exception
- WHEN `OllamaGeneratorAdapter.generate(prompt)` is called
- THEN it raises `LanguageModelUnavailable`

#### Scenario: Adapter is the sole Ollama import site

- GIVEN the full set of new files introduced by this slice
- WHEN their imports are inspected
- THEN only `ollama_generator_adapter.py` imports `ollama`; no domain or
  application file does

### Requirement: QualityDimension Enum

`QualityDimension` (`src/domain/enums/quality_dimension.py`) MUST define exactly 4
members corresponding to the 4 scored dimensions: `CLARITY = "claridad"`,
`COHERENCE = "coherencia"`, `ARGUMENTATION = "argumentacion"`,
`CONCLUSIONS = "conclusiones"`. Member names are English identifiers (this enum
is new in the migration, not legacy-carried vocabulary); `.value` strings stay
in Spanish because they are matched literally against the LLM's Spanish-language
response headers. It MUST NOT reuse or modify the existing `AnalysisDimension`
enum.

#### Scenario: Enum has exactly the 4 expected members

- GIVEN the `QualityDimension` enum
- WHEN its members are enumerated
- THEN there are exactly 4: `CLARITY`, `COHERENCE`, `ARGUMENTATION`,
  `CONCLUSIONS`, with `.value`s `"claridad"`, `"coherencia"`, `"argumentacion"`,
  `"conclusiones"` respectively

#### Scenario: AnalysisDimension is left untouched

- GIVEN the existing `AnalysisDimension` enum
- WHEN this slice is applied
- THEN `AnalysisDimension`'s definition is unchanged and `QualityDimension` does
  not inherit from or alias it

### Requirement: QualityAnalyzer Domain Service Is a Thin Orchestrator

`QualityAnalyzer` (`src/domain/quality/quality_analyzer.py`) MUST be a stateless
domain service, and MUST be the only class defined in that file (one-class-per-file).
Its constructor MUST accept exactly 4 collaborators: an injected `LlmGeneratorPort`
instance, an injected `QualityTextSampler` instance, an injected
`QualityResponseParser` instance, and the two prompt template strings
(`clarity_coherence_prompt_template: str`, `argumentation_conclusions_prompt_template: str`
— see Prompt Template Injection below). It MUST NOT import `ollama`, anything from
`src/infrastructure/`, or perform any file I/O. `analyze()` MUST delegate text
sampling to `QualityTextSampler.build_sample()`, render both prompt templates via
a single private helper that formats an injected template with the sample text,
call `generate()` on the port exactly twice (once per rendered prompt), delegate
parsing of each response to `QualityResponseParser.parse()`, assign dimensions
directly from each call's parsed result, average the 4 final dimension scores into
`overall_score`, map it to a `QualityLevel` via `get_quality_level_from_score()`,
and return a `QualityResultDTO`. It keeps the `QualityAnalysisFailed`-raising
validation that checks whether a call produced any usable (non-fully-defaulted)
content for its relevant dimension pair.

#### Scenario: Domain service has zero infrastructure imports

- GIVEN the `quality_analyzer.py` source file
- WHEN its import statements are inspected
- THEN none import from `src/infrastructure/` or `ollama`

#### Scenario: Port is called exactly twice per analysis

- GIVEN a fake `LlmGeneratorPort` test double that records call count
- WHEN `QualityAnalyzer.analyze(document_content, article_type)` is invoked once
- THEN the fake port's `generate()` method was called exactly 2 times

#### Scenario: quality_analyzer.py defines exactly one class

- GIVEN the `quality_analyzer.py` source file
- WHEN its top-level class definitions are inspected
- THEN exactly one class, `QualityAnalyzer`, is defined — `_DimensionScore` and
  `_ParsedResponse` no longer live in this file

### Requirement: QualityTextSampler Owns Text-Sampling Logic

`QualityTextSampler` (`src/domain/quality/quality_text_sampler.py`) MUST be the
sole owner of the legacy text-sampling heuristic, exposed via a single public
method `build_sample(document_content: DocumentContentDTO) -> str`. Its
constructor MUST accept `min_sample_word_count: int = 400`,
`text_sample_character_limit: int = 8000`, `reference_line_prefix_length: int = 80`,
`introduction_paragraph_count: int = 3`, `middle_paragraph_count: int = 2`,
`conclusion_paragraph_limit: int = 3`, and `fallback_tail_paragraph_count: int = 2`
as plain constructor parameters with defaults matching legacy behavior — the class
itself MUST NOT call `os.getenv`, `load_dotenv`, or perform any environment/file
access; resolving any of these into env-sourced values is a wiring-layer concern
(PR-B), and which subset actually gets exposed via `.env` is a PR-B decision, not
a constraint on this constructor. `build_sample` MUST reproduce the legacy
heuristic exactly: title + first `introduction_paragraph_count` paragraphs (intro)
+ `middle_paragraph_count` middle paragraphs + up to `conclusion_paragraph_limit`
conclusion paragraphs (detected via case-insensitive `conclusi` regex match,
excluding lines whose first `reference_line_prefix_length` characters contain any
`ReferenceLineMarker` value), or, if no conclusion paragraphs are found, the last
`fallback_tail_paragraph_count` non-reference paragraphs. The assembled sample MUST be truncated to
`text_sample_character_limit` characters. If the resulting sample has fewer than
`min_sample_word_count` words, it MUST fall back to the full joined paragraph text
(also truncated to `text_sample_character_limit`) instead of the sample.
Conclusion/reference-line detection helpers (previously
`_collect_conclusion_or_tail_paragraphs`, `_is_reference_like`) are private methods
scoped to this class alone.

#### Scenario: Short document triggers full-text fallback instead of sampling

- GIVEN a document whose strategically sampled text totals fewer than
  `min_sample_word_count` words
- WHEN `QualityTextSampler.build_sample(document_content)` is called
- THEN it returns the full joined paragraph text (truncated to
  `text_sample_character_limit` characters) instead of the sampled excerpt

#### Scenario: Long document uses the strategic sample, not full text

- GIVEN a document whose strategically sampled text totals
  `min_sample_word_count` words or more
- WHEN `QualityTextSampler.build_sample(document_content)` is called
- THEN it returns the sampled excerpt (title + intro + middle + conclusion or
  fallback tail paragraphs), not the full document text

#### Scenario: Conclusion detection excludes reference-like lines

- GIVEN paragraphs after a detected "conclusi..." paragraph where some lines'
  first 80 characters contain a value matching one of the `ReferenceLineMarker`
  members
- WHEN `QualityTextSampler` collects conclusion paragraphs for the sample
- THEN those reference-like lines are excluded from the collected conclusion
  paragraphs

#### Scenario: Word count and character limit are constructor-tunable

- GIVEN a `QualityTextSampler` constructed with
  `min_sample_word_count=10, text_sample_character_limit=500`
- WHEN `build_sample(document_content)` is called
- THEN the fallback-to-full-text decision uses `10` as the word-count threshold
  and the result is truncated to `500` characters, not the legacy defaults

### Requirement: ReferenceLineMarker Enum Replaces the Reference-Line Tuple

`ReferenceLineMarker` (`src/domain/enums/reference_line_marker.py`) MUST be an
`Enum` with exactly 4 members: `HTTP = "http"`, `DOI = "doi.org"`,
`HTTPS = "https"`, `ISBN = "ISBN"`. `QualityTextSampler`'s reference-line detection
MUST check membership via `any(marker.value in paragraph[:80] for marker in
ReferenceLineMarker)`, replacing the legacy private tuple constant.

#### Scenario: Enum has exactly the 4 expected markers

- GIVEN the `ReferenceLineMarker` enum
- WHEN its members are enumerated
- THEN there are exactly 4: `HTTP`, `DOI`, `HTTPS`, `ISBN`, with values `"http"`,
  `"doi.org"`, `"https"`, `"ISBN"` respectively

### Requirement: Prompt Template Injection — Domain Stays File-I/O-Free

The two prompt templates (Call 1: Claridad + Coherencia; Call 2: Argumentación +
Conclusiones) MUST live as plain text files at
`src/infrastructure/resources/prompts/quality/clarity_coherence_prompt.txt` and
`src/infrastructure/resources/prompts/quality/argumentation_conclusions_prompt.txt`,
preserving the legacy's exact Spanish wording, instructions, response format
headers, and scoring criteria line, with a `{text_sample}` placeholder (Python
`.format()` style) where the sample text is interpolated. `QualityAnalyzer` MUST
receive both template strings as constructor parameters
(`clarity_coherence_prompt_template: str`,
`argumentation_conclusions_prompt_template: str`) and MUST render each via a
single private helper (e.g. `_render_prompt(template: str, text_sample: str) ->
str`) that calls `.format(text_sample=...)` on the injected template — this
collapses the legacy's two near-duplicate `_build_prompt_one`/`_build_prompt_two`
methods into one, since both were doing identical template-formatting work. Zero
file I/O exists anywhere in `src/domain/`; reading these 2 files from disk and
passing their contents into `QualityAnalyzer`'s constructor is a PR-B wiring
concern (see "Updated Dependencies for PR-B" below). PR-A's domain tests construct
`QualityAnalyzer` with literal template strings directly — no file I/O in domain
tests either.

#### Scenario: Rendered prompt preserves legacy wording with sample interpolated

- GIVEN a `QualityAnalyzer` constructed with a literal Claridad/Coherencia
  template string containing `{text_sample}` and the legacy Spanish instructions
- WHEN `analyze()` renders the Call 1 prompt
- THEN the rendered prompt contains the legacy Spanish wording verbatim with the
  built text sample substituted in place of `{text_sample}`

#### Scenario: Two prompt-building methods collapse into one

- GIVEN the `quality_analyzer.py` source file
- WHEN its methods are inspected
- THEN there is no `_build_prompt_one` or `_build_prompt_two` method; a single
  private template-rendering helper is used for both calls

### Requirement: QualityResponseParser Owns Per-Dimension Response Parsing

`QualityResponseParser` (`src/domain/quality/quality_response_parser.py`) MUST be
the sole owner of response-parsing logic, exposed via a single public method
`parse(response_text: str) -> ParsedResponseDTO`. The 3 regex patterns
(`_DIMENSION_HEADER_PATTERN`, `_EXPLICIT_SCORE_PATTERN`,
`_RECOMMENDATION_TAIL_PATTERN`) remain named module-level constants in this file —
they are not enums; a compiled regex is not a categorical value. The 2 single-default
values (`unscored_dimension_score`, `unscored_dimension_feedback`) are constructor
parameters defaulting to `7.0` and `"No disponible"` respectively (not module
constants) — consistent with `QualityTextSampler`'s tunables, so future `.env`
sourcing happens via infrastructure-injected constructor arguments, never via the
domain reading `os`/`dotenv` directly. `_NARRATIVE_SCORE_KEYWORDS` (in `src/domain/quality/dimension_score_extractor.py`) stays a named
module-level constant, following the same pattern as the existing module-level keyword table
`_DIMENSION_KEYWORDS` in `src/domain/quality/quality_dimension_matcher.py`.
`_map_block_to_dimension` uses a declarative `_DIMENSION_KEYWORDS` lookup table
(dimension → keyword tuple) instead of an if/elif chain, mirroring
`_NARRATIVE_SCORE_KEYWORDS`'s shape. `parse()` MUST preserve the
following rules exactly for a single LLM response string:

- Split the response into blocks on dimension headers matching
  `\*\*(?:\d+\.\s*)?(?:Claridad|Coherencia|Argumentaci[oó]n|Conclusiones)` with
  case-insensitive matching, supporting both numbered (`**1. Claridad`) and
  unnumbered (`**Claridad`) header formats.
- For each non-empty block, search for an explicit score using
  `\[Puntuaci[oó]n:\s*(\d+(?:\.\d+)?)(?:/10)?\]` or `(\d+(?:\.\d+)?)\s*/\s*10`
  (case-insensitive). If found, clamp the parsed float to the `[0.0, 10.0]` range.
- If no explicit score is found, infer one from narrative keywords in the
  lowercased block: `excelente`/`sobresaliente`/`muy bueno` → `8.5`;
  `bueno`/`adecuado`/`correcto` → `7.5`; `aceptable`/`suficiente`/`regular` →
  `6.0`; `deficiente`/`débil`/`pobre`/`insuficiente` → `4.0`; otherwise a neutral
  default score.
- Build feedback from all non-empty lines after the header line, joined by
  spaces, with any `**RECOMENDACIÓN...` tail stripped (case-insensitive, across
  newlines) and whitespace collapsed. If the resulting feedback is shorter than
  10 characters, replace it with a named neutral "not available" feedback
  constant. Truncate feedback to at most 3 sentences (split on `.`, rejoined with
  `. ` and a trailing `.`).
- Map each parsed block to a dimension by inspecting the first 200 characters of
  the block (case-insensitive), checking in this order: `argumentaci` →
  `ARGUMENTATION`; else `conclusi` → `CONCLUSIONS`; else `coherencia` →
  `COHERENCE`; else `claridad` or `argumento` → `CLARITY`. (Order matters: the
  `argumentaci` check MUST run before the `claridad`/`argumento` check to avoid a
  false match on the substring `argumento` inside `argumentacion`.)
- Any dimension not matched by any block in the response keeps a named neutral
  default score and feedback for that dimension only.

#### Scenario: Numbered and unnumbered headers both parse correctly

- GIVEN one response using `**1. Claridad del argumento** [Puntuación: 8/10]` and
  another using `**Claridad** [Puntuación: 8/10]`
- WHEN each is parsed
- THEN both produce a Claridad score of `8.0` with the same feedback extraction
  rules applied

#### Scenario: Score inferred from narrative when explicit score is absent

- GIVEN a block whose text contains "el argumento es bastante bueno y adecuado"
  with no `[Puntuación: X/10]` or `X/10` pattern present
- WHEN the block is parsed
- THEN the inferred score is `7.5`

#### Scenario: Feedback shorter than 10 characters becomes the neutral default

- GIVEN a parsed block whose extracted feedback text is fewer than 10 characters
  long
- WHEN parsing completes for that block
- THEN the feedback is replaced with the named neutral "not available" feedback
  constant

#### Scenario: Feedback longer than 3 sentences is truncated

- GIVEN a parsed block whose feedback contains 5 sentences
- WHEN parsing completes for that block
- THEN the stored feedback contains only the first 3 sentences, joined with
  `". "` and ending in `"."`

#### Scenario: Argumentacion is not misclassified as Claridad

- GIVEN a block whose first 200 characters contain both `argumentaci` and the
  word `argumento`
- WHEN the block is mapped to a dimension
- THEN it is mapped to `ARGUMENTATION`, not `CLARITY`

#### Scenario: One missing dimension in an otherwise valid response keeps the rest

- GIVEN a Call 1 response with a valid Claridad block but no Coherencia header
  anywhere in the text
- WHEN the response is parsed
- THEN Claridad reflects the parsed score and feedback, and Coherencia falls back
  to the named neutral default score and feedback — parsing for that call does
  not fail

### Requirement: DimensionScoreDTO and ParsedResponseDTO Extracted as Domain DTOs

`DimensionScoreDTO` (`src/domain/dtos/dimension_score_dto.py`) MUST be a
`@dataclass(frozen=True)` extending `BaseDTO` with fields `score: float` and
`feedback: str`, replacing the legacy private `_DimensionScore` dataclass.
`ParsedResponseDTO` (`src/domain/dtos/parsed_response_dto.py`) MUST be a
`@dataclass(frozen=True)` extending `BaseDTO` with fields
`scores: dict[QualityDimension, DimensionScoreDTO]` and
`matched_dimensions: frozenset[QualityDimension]`, replacing the legacy private
`_ParsedResponse` dataclass. `QualityResponseParser.parse()` MUST return a
`ParsedResponseDTO`, and its internal per-block score/feedback pairs MUST be
`DimensionScoreDTO` instances.

#### Scenario: DimensionScoreDTO and ParsedResponseDTO extend BaseDTO

- GIVEN `DimensionScoreDTO` and `ParsedResponseDTO`
- WHEN their class hierarchies are inspected
- THEN both are frozen dataclasses extending `BaseDTO`, and neither class is
  defined inside `quality_analyzer.py`

### Requirement: Direct Per-Call Dimension Assignment, No Cross-Call Heuristic

`QualityAnalyzer` MUST assign `CLARITY` and `COHERENCE` directly from Call 1's
`ParsedResponseDTO` (produced by `QualityResponseParser.parse()`), and
`ARGUMENTATION` and `CONCLUSIONS` directly from Call 2's `ParsedResponseDTO`. It
MUST NOT apply any cross-call fallback or "prefer whichever call has real
feedback" heuristic — each dimension has exactly one authoritative source call.

#### Scenario: Claridad and Coherencia always come from Call 1

- GIVEN a Call 1 response containing valid Claridad and Coherencia scores and a
  Call 2 response that (hypothetically) also contains text matching a Claridad
  header
- WHEN dimension scores are assembled
- THEN the final Claridad and Coherencia scores are taken from Call 1's parsed
  result, never from Call 2

#### Scenario: Argumentacion and Conclusiones always come from Call 2

- GIVEN a Call 2 response containing valid Argumentacion and Conclusiones scores
- WHEN dimension scores are assembled
- THEN the final Argumentacion and Conclusiones scores are taken from Call 2's
  parsed result, never from Call 1

### Requirement: Full Per-Call Parse Failure Raises QualityAnalysisFailed

If, for a single call's response, all 4 dimensions for that call's relevant pair
fail to parse such that the entire response yields only neutral-default values
with no genuine extracted content (i.e. the response could not be parsed in any
usable way), `QualityAnalyzer` MUST raise `QualityAnalysisFailed` instead of
returning a result built from defaults. Partial failure — where at least one
dimension in a call's response parses successfully — MUST NOT raise; only the
failing dimension(s) fall back to the named neutral default.

#### Scenario: Both dimensions in one call's response fail to parse

- GIVEN Call 1's response text contains neither a Claridad header nor a
  Coherencia header anywhere, and no parseable score/feedback content for either
- WHEN `QualityAnalyzer.analyze(...)` processes Call 1's response
- THEN it raises `QualityAnalysisFailed`

#### Scenario: Partial failure in one call does not raise

- GIVEN Call 1's response contains a valid, parseable Claridad block but no
  Coherencia header
- WHEN `QualityAnalyzer.analyze(...)` processes Call 1's response
- THEN no exception is raised; Claridad uses the parsed value and Coherencia uses
  the named neutral default

### Requirement: Overall Score and Quality Level Computation

`QualityAnalyzer` MUST compute `overall_score` as the arithmetic mean of the 4
final dimension scores, and MUST map that mean to a `QualityLevel` using
`get_quality_level_from_score` (`src/domain/enums/quality_level.py`), unchanged:
`>= 9.0` → `EXCELLENT`; `>= 7.0` → `GOOD`; `>= 5.0` → `ACCEPTABLE`; `>= 3.0` →
`NEEDS_IMPROVEMENT`; otherwise `POOR`. The `QualityLevel` enum's body and its
`.value` members (used as printable strings in `QualityResultDTO.__str__`) MUST
NOT be modified by this slice; the 4 numeric thresholds remain expressed as a
named module-level constant used inside `get_quality_level_from_score()`, not as
enum values. The result MUST be returned as a `QualityResultDTO` (reused as-is, no
new DTO), with `dimension_scores` keyed by the 4 dimension string values mirroring
the legacy's dict shape.

#### Scenario: Overall score is the mean of the 4 dimension scores

- GIVEN final dimension scores of `8.0, 6.0, 7.0, 9.0`
- WHEN `overall_score` is computed
- THEN it equals `7.5`

#### Scenario: Quality level boundaries match legacy thresholds

- GIVEN an `overall_score` of exactly `7.0`
- WHEN `quality_level` is computed
- THEN it resolves to `QualityLevel.GOOD`

#### Scenario: QualityLevel enum body is untouched

- GIVEN the `QualityLevel` enum definition
- WHEN this slice is applied
- THEN its 5 members and their string `.value`s are unchanged, and no threshold
  numbers are added as enum values

### Requirement: Tunable Sampling Values Are Constructor Parameters, Not Domain Env Reads

All sampling-related tunable values — minimum sample word count, text sample
character limit, reference-line prefix length, and the 4 paragraph-slicing
counts (introduction, middle, conclusion limit, fallback tail) — MUST be exposed
as `QualityTextSampler` constructor parameters (`min_sample_word_count: int =
400`, `text_sample_character_limit: int = 8000`, `reference_line_prefix_length:
int = 80`, `introduction_paragraph_count: int = 3`, `middle_paragraph_count: int
= 2`, `conclusion_paragraph_limit: int = 3`, `fallback_tail_paragraph_count: int
= 2`) with defaults matching legacy behavior. The 2 single-default values on
`QualityResponseParser` (`unscored_dimension_score: float = 7.0`,
`unscored_dimension_feedback: str = "No disponible"`) follow the same rule.
Neither class MUST call `os.getenv` or `load_dotenv`, nor import `python-dotenv`
or `os.environ` — resolving any subset of these into environment variables (via
`python-dotenv`, added to `requirements.txt`, with a `.env.example` documenting
the chosen vars and their defaults) into these constructor parameters is a
wiring-layer (PR-B) concern, kept out of `src/domain/` entirely. Which of these
parameters PR-B actually exposes via `.env` (versus leaving at their constructor
default) is a PR-B design decision, not constrained by this requirement.

#### Scenario: QualityTextSampler has zero environment or dotenv imports

- GIVEN the `quality_text_sampler.py` source file
- WHEN its import statements are inspected
- THEN none import `os`, `dotenv`, or any environment-reading module

#### Scenario: Defaults match legacy behavior when no parameters are passed

- GIVEN a `QualityTextSampler` constructed with no arguments
- WHEN `build_sample(document_content)` is called
- THEN it behaves identically to the legacy hardcoded
  `_MINIMUM_SAMPLE_WORD_COUNT = 400` / `_TEXT_SAMPLE_CHARACTER_LIMIT = 8000`
  constants

### Requirement: QualityAnalyzer Is Consumed Directly by the Orchestrator

> **Superseded (2026-07-04, `refactor_analyze_document_wiring`)**: `AnalyzeQualityUseCase`
> and `AnalyzeQualityUseCaseWiring` were eliminated as redundant pass-through layers.
> `AnalyzeDocumentUseCase` now depends on `QualityAnalyzer` directly and calls
> `.analyze(document_content=..., article_type=...)` from its `execute()` method — see
> `openspec/specs/analyze-document/spec.md`. `AnalyzeDocumentUseCaseWiring._get_quality_analyzer()`
> constructs the domain service directly (no intermediate sub-wiring).

`AnalyzeDocumentUseCase` MUST depend on `QualityAnalyzer` directly and call
`analyze(document_content=document_content, article_type=classification.article_type)`
without adding business logic.

#### Scenario: Orchestrator uses the domain service's result unchanged

- GIVEN a `DocumentContentDTO` and an `article_type` value
- WHEN `AnalyzeDocumentUseCase.execute()` calls `self._quality_analyzer.analyze(document_content=document_content, article_type=article_type)`
- THEN the returned `QualityResultDTO` matches what `QualityAnalyzer.analyze`
  would produce for the same `document_content`

### Requirement: AnalyzeDocumentUseCaseWiring Assembles Domain Service and Adapter

`AnalyzeDocumentUseCaseWiring._get_quality_analyzer()` MUST construct `QualityAnalyzer`
directly. It MUST reuse the shared `OllamaGeneratorAdapter` instance from `_get_llm_generator()`
(the same instance injected into `ArticleClassifier` — see classify-article spec) rather than
assembling a second adapter. The wiring MUST NOT contain business logic.

#### Scenario: Wiring produces a usable QualityAnalyzer instance

- GIVEN an `AnalyzeDocumentUseCaseWiring` instance
- WHEN `create_use_case()` is called
- THEN the resulting `AnalyzeDocumentUseCase._quality_analyzer` is a real
  `QualityAnalyzer` backed by a real `OllamaGeneratorAdapter`

#### Scenario: LLM generator instance is shared, not duplicated

- GIVEN `AnalyzeDocumentUseCaseWiring().create_use_case()`
- WHEN the resulting `_article_classifier._llm_generator` and
  `_quality_analyzer._llm_generator` are compared
- THEN they are the exact same object (`is`), not merely equal instances

### Requirement: No print() Statements in Migrated Code

None of the new domain, application, or infrastructure files introduced by this
slice MUST contain a `print()` call. The legacy's 5 Spanish emoji progress
messages are dropped, not replaced with logging, in this slice.

#### Scenario: No print calls anywhere in the new code

- GIVEN the full set of new files introduced by this slice (port, adapter, enum,
  domain service, use case, wiring)
- WHEN their source is inspected
- THEN none contain a `print(` call

## Updated Dependencies for PR-B

This PR-A spec update introduces 2 new obligations for PR-B's
`AnalyzeQualityUseCaseWiring` (not specified here in detail — PR-B's own
design/tasks will define its requirements):

1. Load `clarity_coherence_prompt.txt` and
   `argumentation_conclusions_prompt.txt` from
   `src/infrastructure/resources/prompts/quality/` at wiring-assembly time, and
   pass the loaded template strings into `QualityAnalyzer`'s constructor.
2. Read `QUALITY_MIN_SAMPLE_WORD_COUNT` and
   `QUALITY_TEXT_SAMPLE_CHARACTER_LIMIT` via `python-dotenv`, and pass the
   resolved integers into `QualityTextSampler`'s constructor.

No other PR-B scope (adapter, use case shape) changes as a result of this
update.

## Out of Scope

- `self.client = ollama.Client(...)` field from legacy `__init__` — built but
  never used (only `self.ollama.generate()` is called). Not carried into the
  adapter; tracked in `migration/dead-code-registry`.
- Module-level `analyze_document_quality()` convenience function — confirmed
  broken (calls the instance method with 3 positional arguments against a 2-arg
  signature), unreachable, and excluded entirely.
- Wiring `AnalyzeQualityUseCase` into `main.py` — deferred to the
  caller-switchover slice; legacy `business_logic/quality_analyzer.py` keeps
  serving production calls during coexistence.
- Deleting `business_logic/quality_analyzer.py` — coexistence maintained until
  the caller-switchover slice.
- Replacing dropped `print()` progress messages with structured logging — not
  introduced in this slice.
