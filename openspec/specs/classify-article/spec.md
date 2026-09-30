# Article Classification Specification

## Purpose

Deterministic-plus-LLM-backed classification of a document into `ArticleType`
(CIENTIFICO/DIVULGACION/OPINION), producing a `ClassificationResultDTO` (type,
size, confidence, reasoning) via a 19-case rule table fed by 6 signals — 5 of
them pure/local, one LLM-backed (a single combined call extracting 3 yes/no
answers). Second capability in the migration with an external dependency;
proves `LlmGeneratorPort` (established in `analyze-quality`, Slice 5)
generalizes to a second consumer via an additive port extension rather than a
new port.

## Requirements

### Requirement: IMRyD Signal Detector — Deterministic Section-Keyword Presence

A domain service (exact class/file name finalized in design; MUST NOT be named
`StructureAnalyzer` — see "Naming Collision Avoidance" below) MUST detect the
presence of IMRyD section keywords in a document's paragraphs and return a
boolean signal dict, ported verbatim from legacy `StructureAnalyzer.analyze()`.
It MUST scan only short paragraphs (1 to 5 words after stripping) as section
header candidates, matching against the bilingual `IMRYD_KEYWORDS` table
(introduction/methods/results/discussion/conclusion, each with English and
Spanish keyword variants) using case-insensitive substring matching. The
returned dict MUST contain exactly 6 boolean keys:
`has_introduction`, `has_methods`, `has_results`, `has_discussion`,
`has_conclusion`, and `imryd_complete`. `imryd_complete` MUST be `True` if and
only if `has_introduction`, `has_methods`, `has_results`, and `has_discussion`
are all `True` — `has_conclusion` MUST NOT be a factor in `imryd_complete`,
even though it is independently detected and returned.

#### Scenario: Long body paragraphs are never treated as section headers

- GIVEN a document paragraph longer than 5 words that happens to contain the
  word "introducción" or "results" inside body prose
- WHEN the signal detector scans for section headers
- THEN that paragraph is excluded from header-candidate matching and does not
  set the corresponding `has_*` signal to `True`

#### Scenario: All 4 core sections present yields imryd_complete True

- GIVEN a document with short header paragraphs matching introduction,
  methods, results, and discussion keywords, with no conclusion header
- WHEN the signal detector runs
- THEN `has_introduction`, `has_methods`, `has_results`, and `has_discussion`
  are all `True`, `has_conclusion` is `False`, and `imryd_complete` is `True`

#### Scenario: Conclusion presence alone does not satisfy imryd_complete

- GIVEN a document with a short header paragraph matching a conclusion
  keyword but missing one or more of introduction, methods, results, or
  discussion headers
- WHEN the signal detector runs
- THEN `has_conclusion` is `True` but `imryd_complete` is `False`

#### Scenario: Bilingual keyword matching covers Spanish and English variants

- GIVEN a document whose short header paragraphs use Spanish section names
  (e.g. "Metodología", "Resultados", "Discusión")
- WHEN the signal detector runs
- THEN the corresponding `has_methods`, `has_results`, and `has_discussion`
  signals are `True`, identically to an equivalent document using the English
  section names

### Requirement: Naming Collision Avoidance with StructureValidator

The migrated IMRyD signal-detection class MUST NOT be named `StructureAnalyzer`.
This name is reserved against collision with the unrelated, already-migrated
`StructureValidator` (`src/domain/structure/structure_validator.py`, from the
`validate-structure` slice), which solves a different problem (per-`ArticleType`
required-section completeness, producing `(present, missing)` lists) than this
service (deterministic boolean signal detection consumed only by
classification). The final class/file name is finalized in design; this
requirement constrains only what it must NOT be.

#### Scenario: No class named StructureAnalyzer exists in src/domain

- GIVEN the full set of new files introduced by this slice
- WHEN their class definitions are inspected
- THEN no class is named `StructureAnalyzer` anywhere under `src/domain/`

#### Scenario: StructureValidator is unmodified

- GIVEN `src/domain/structure/structure_validator.py`
- WHEN this slice is applied
- THEN its class definition, `_SECTION_ALIASES` table, and `validate()`
  behavior are unchanged

### Requirement: LlmGeneratorPort Gains an Additive Options Parameter

`LlmGeneratorPort` (`src/domain/ports/llm_generator_port.py`) MUST extend its
single method's signature from `generate(self, prompt: str) -> str` to
`generate(self, prompt: str, options: dict | None = None) -> str`. The new
parameter MUST default to `None` so that existing `analyze-quality` call sites
calling `generate(prompt)` positionally remain valid with no source changes.
`OllamaGeneratorAdapter.generate()` MUST forward `options` to
`ollama.generate(options=options)` unmodified, with no adapter-side
interpretation, defaulting, or translation of the dict's contents.

#### Scenario: Existing analyze-quality call site is unaffected

- GIVEN `QualityAnalyzer`'s existing calls to `self._llm_generator.generate(prompt)`
  with no `options` argument
- WHEN this slice's port signature change is applied
- THEN those call sites continue to compile and behave identically — no
  changes to `quality_analyzer.py` or its tests are required

#### Scenario: Options dict forwards to ollama.generate verbatim

- GIVEN a call to `OllamaGeneratorAdapter.generate(prompt, options={"temperature": 0.1, "num_predict": 300})`
- WHEN the adapter executes
- THEN the underlying `ollama.generate()` call receives
  `options={"temperature": 0.1, "num_predict": 300}` unchanged

#### Scenario: Omitting options preserves prior adapter behavior

- GIVEN a call to `OllamaGeneratorAdapter.generate(prompt)` with no `options`
  argument
- WHEN the adapter executes
- THEN the underlying `ollama.generate()` call is made exactly as it was
  before this slice (no `options` kwarg forced upon it with a non-`None`
  default)

### Requirement: ArticleClassifier Domain Service Orchestrates Classification

> **Superseded (Phase 3 Laya System 1 integration, TASK-16)**: In Phase 3 Laya System 1
> integration (TASK-16), S4, S5, and S6 are derived directly from `laya_decision: LayaDecisionResultDTO`
> (`s4_research_intent`, `s5_empirical_evidence`, `s6_theoretical_framework` mapping
> `LayaBinaryAnswer.YES` to `True`), and the Ollama LLM signal call, prompt, parser, and
> `ARTICLE_CLASSIFIER_TEMPERATURE`/`ARTICLE_CLASSIFIER_NUM_PREDICT` env vars were retired.
> `ArticleClassifier.classify()` receives `(document_content, laya_decision)` and no longer
> depends on `LlmGeneratorPort`.

`ArticleClassifier` (or equivalent name finalized in design) MUST be a domain
service, constructor-injected with an `LlmGeneratorPort` instance, the IMRyD
signal detector, a text sampler, a response parser, and two required
constructor parameters `temperature` and `num_predict` with **no defaults** —
mirroring the `analyze-quality` precedent of tunables having no domain-layer
defaults. It MUST NOT import `ollama`, anything from `src/infrastructure/`, or
perform file I/O. Its public entry point MUST classify a `DocumentContentDTO`
into a `ClassificationResultDTO` by: computing `ArticleSize` via
`classify_article_size()`; checking the IMRyD override path first; if not
overridden, computing the 5 remaining signals (reference count, reference
recency, methodological vocabulary, and the combined S4/S5/S6 LLM call); and
applying the 19-case rule table to produce the final result. The LLM call MUST
pass `options={"temperature": self._temperature, "num_predict": self._num_predict}`
to the port's `generate()`.

#### Scenario: Constructor requires temperature and num_predict with no defaults

- GIVEN an attempt to construct `ArticleClassifier` without supplying
  `temperature` or `num_predict`
- WHEN the constructor is inspected or called
- THEN it raises a `TypeError` for the missing required argument — neither
  parameter has a default value

#### Scenario: Domain service has zero infrastructure imports

- GIVEN the file defining `ArticleClassifier`
- WHEN its import statements are inspected
- THEN none import from `src/infrastructure/` or `ollama`

#### Scenario: LLM call passes temperature and num_predict as options

- GIVEN an `ArticleClassifier` constructed with `temperature=0.1` and
  `num_predict=300`, and a fake `LlmGeneratorPort` test double that records
  call arguments
- WHEN classification reaches the S4/S5/S6 signal-extraction call
- THEN the fake port's `generate()` was called with
  `options={"temperature": 0.1, "num_predict": 300}`

#### Scenario: IMRyD override short-circuits the remaining 5 signals

- GIVEN a document whose IMRyD signal detector returns `imryd_complete=True`
  and whose `ArticleSize` is not `FUERA_RANGO`
- WHEN `ArticleClassifier` classifies the document
- THEN the result is `ArticleType.CIENTIFICO` with confidence
  `ClassificationConfidence.IMRYD_OVERRIDE` (0.95) without computing
  reference-count, reference-recency, methodological-vocabulary, or LLM
  signals

#### Scenario: IMRyD complete but article size out of range does not override

- GIVEN a document whose IMRyD signal detector returns `imryd_complete=True`
  but whose `ArticleSize` is `FUERA_RANGO`
- WHEN `ArticleClassifier` classifies the document
- THEN the IMRyD override does NOT apply, and classification proceeds to
  compute the remaining 5 signals and apply the 19-case rule table

### Requirement: Dedicated Classification Text Sampler

A text sampler distinct from `QualityTextSampler` MUST own the legacy
`_build_text_sample()` heuristic for the S4/S5/S6 LLM call, exposed as an
injectable unit with its own sampling algorithm. It MUST take the first 3500
characters and last 2500 characters of the document's joined paragraph text,
excluding any bibliography section detected via a short paragraph (at most 30
characters) containing one of the bibliography markers ("referencias",
"bibliografía", "bibliography", "fuentes bibliográficas"). If the resulting
sample is empty, it MUST fall back to the first 6000 characters of the full
joined text.

#### Scenario: Bibliography section is excluded from the sample

- GIVEN a document whose paragraphs include a short standalone paragraph
  "Referencias" followed by bibliography entries
- WHEN the sampler builds the text sample
- THEN none of the text after the "Referencias" marker paragraph is included
  in the sample

#### Scenario: Sample combines intro and ending segments

- GIVEN a document whose bibliography-excluded text exceeds 6000 characters
- WHEN the sampler builds the text sample
- THEN the result is the first 3500 characters concatenated with the last
  2500 characters of that bibliography-excluded text

#### Scenario: Empty sample falls back to first 6000 characters of full text

- GIVEN a document whose bibliography-excluded text reduces to an empty
  string
- WHEN the sampler builds the text sample
- THEN the result is the first 6000 characters of the full joined paragraph
  text (including any bibliography)

### Requirement: S4/S5/S6 Response Parser

> **Superseded (Phase 3 Laya System 1 integration, TASK-16)**: The Ollama LLM signal call,
> prompt, and response parser were retired. S4, S5, and S6 are derived directly from
> `laya_decision: LayaDecisionResultDTO` (`s4_research_intent`, `s5_empirical_evidence`,
> `s6_theoretical_framework` mapping `LayaBinaryAnswer.YES` to `True`).

A response parser MUST extract 3 independent yes/no booleans (S4: explicit
research intent; S5: evidence-based conclusive contribution; S6: theoretical
framework justification or knowledge-gap identification) from a single
free-text LLM response, using case-insensitive regex matching for the
patterns `S4\s*:\s*SI`, `S5\s*:\s*SI`, and `S6\s*:\s*SI` against the
uppercased response text. Each of S4, S5, S6 MUST be `True` only if its
corresponding pattern matches; absence of a match (including malformed or
partial responses) MUST yield `False` for that signal, not raise an
exception.

#### Scenario: Well-formed response parses all 3 signals correctly

- GIVEN an LLM response containing the lines `S4: SI`, `S5: NO`, `S6: SI`
- WHEN the response parser parses it
- THEN it returns `(True, False, True)` for `(s4, s5, s6)`

#### Scenario: Malformed response yields all-False without raising

- GIVEN an LLM response that contains none of the expected `S4:`/`S5:`/`S6:`
  markers
- WHEN the response parser parses it
- THEN it returns `(False, False, False)` without raising an exception

### Requirement: Reference-Count and Reference-Recency Signals Are Ported Verbatim

The reference-count signal (S2a) MUST be `True` if and only if the document
has 12 or more references. The reference-recency signal (S2b) MUST be `True`
if and only if at least 50% of references have an extracted year (via regex
`\b((?:19|20)\d{2})\b` against each reference's text, using the maximum year
found per reference) greater than or equal to the current year minus 4. Both
signals MUST be `False` when the document has no references.

#### Scenario: Reference count signal fires at exactly 12 references

- GIVEN a document with exactly 12 references
- WHEN the reference-count signal is computed
- THEN it is `True`

#### Scenario: Reference count signal does not fire at 11 references

- GIVEN a document with exactly 11 references
- WHEN the reference-count signal is computed
- THEN it is `False`

#### Scenario: Reference recency signal uses the maximum year per reference

- GIVEN a reference whose text contains both "1998" and "2024"
- WHEN the reference-recency signal evaluates that reference's recency
- THEN it treats that reference as having year `2024`, not `1998`

#### Scenario: No references yields False for both reference signals

- GIVEN a document with an empty references list
- WHEN both reference signals are computed
- THEN both are `False`

### Requirement: Methodological Vocabulary Signal Is Ported Verbatim

The methodological-vocabulary signal (S3) MUST be `True` if and only if at
least 4 distinct terms from the methodological vocabulary list are found in
the document's full text (Unicode-normalized, accent-insensitive,
case-insensitive matching) AND at least 1 of those found terms is also a
member of the "hard terms" subset. Finding 4 or more general terms with zero
hard terms present MUST yield `False`.

#### Scenario: Four general terms with one hard term satisfies S3

- GIVEN document text containing 4 distinct methodological-vocabulary terms,
  at least 1 of which is a hard term (e.g. "análisis estadístico")
- WHEN the methodological-vocabulary signal is computed
- THEN it is `True`

#### Scenario: Four general terms with zero hard terms does not satisfy S3

- GIVEN document text containing 4 distinct methodological-vocabulary terms,
  none of which are hard terms
- WHEN the methodological-vocabulary signal is computed
- THEN it is `False`

#### Scenario: Accent-insensitive matching treats accented and unaccented terms identically

- GIVEN document text containing "metodologia" (unaccented) where the
  vocabulary list entry is "metodología" (accented)
- WHEN term matching is performed
- THEN the term counts as found regardless of the accent difference

### Requirement: 19-Case Rule Table Produces Identical Output to Legacy

Given the 6 signals `(s2a, s2b, s3, s4, s5, s6)` — reference count, reference
recency, methodological vocabulary, research intent, evidentiary contribution,
theoretical justification — the rule table MUST produce the exact same
`(article_type, confidence, reasoning)` triple as legacy
`business_logic/article_classifier.py`'s `_apply_rule` method, with no
reinterpretation of branch conditions, confidence values, or reasoning text.
The legacy IMRyD override (case 1, handled separately before `_apply_rule` is
invoked) plus `_apply_rule`'s 18 branches form the full 19-case table:

| Case | Condition | Result | Confidence |
|------|-----------|--------|------------|
| 1 | IMRyD override (`imryd_complete` AND size != FUERA_RANGO) | CIENTIFICO | 0.95 |
| 2 | s3∧s4∧s5∧s2a∧s2b∧s6 | CIENTIFICO | 0.90 |
| 3 | s3∧s4∧s5∧s2b∧s6 (not case 2) | CIENTIFICO | 0.86 |
| 4 | s3∧s4∧s5∧s2a∧s2b (not case 2/3) | CIENTIFICO | 0.85 |
| 5 | s3∧s4∧s5∧s2a∧s6 (not case 2/3/4) | CIENTIFICO | 0.83 |
| 6 | s3∧s4∧s5∧s6, none of cases 2-5 matched | DIVULGACION (near-miss) | None |
| 7 | s3∧s4∧s5∧s2b, none of cases 2-6 matched | DIVULGACION (near-miss) | None |
| 8 | s3∧s4∧s5∧s2a, none of cases 2-7 matched | DIVULGACION (near-miss) | None |
| 9 | s3∧s4∧s5, none of cases 2-8 matched | DIVULGACION (near-miss) | None |
| 10 | s3∧s4 (not full s3∧s4∧s5 branch) | DIVULGACION | None |
| 11 | s3∧s5 (not full s3∧s4∧s5 branch, not case 10) | DIVULGACION | None |
| 12 | s3∧s2a∧s2b (not cases 9-11) | DIVULGACION | None |
| 13 | s3∧s2a (not cases 9-12) | DIVULGACION | None |
| 14 | s3∧s2b (not cases 9-13) | DIVULGACION | None |
| 15 | s3 only (not cases 9-14) | DIVULGACION | None |
| 16 | s4∧s5 (not s3) | DIVULGACION | None |
| 17 | s4 only (not s3, not s5) | DIVULGACION | None |
| 18 | s5 only (not s3, not s4) | DIVULGACION | None |
| 19 | none of the above match | OPINION | None |

The condition evaluation order MUST match legacy exactly — branches are
checked top-to-bottom with early return, so e.g. case 10 (`s3∧s4`) is reached
only when the full `s3∧s4∧s5` branch (cases 2-9) did not match, and case 17
(`s4` only) is reached only after cases 10 and 16 are ruled out. Per-branch
Spanish-prose `reasoning` strings MUST be preserved verbatim, character for
character, from the legacy implementation. DIVULGACION and OPINION results
MUST carry `confidence=None`; confidence values apply exclusively to
CIENTIFICO results.

#### Scenario: Case 2 — full signal set produces 0.90 confidence

- GIVEN signals `s2a=True, s2b=True, s3=True, s4=True, s5=True, s6=True`
- WHEN the rule table is applied
- THEN the result is `ArticleType.CIENTIFICO` with confidence `0.90` and
  reasoning text identical to legacy case 2's reasoning string

#### Scenario: Case 5 — minimum-threshold CIENTIFICO produces 0.83 confidence

- GIVEN signals `s2a=True, s2b=False, s3=True, s4=True, s5=True, s6=True`
- WHEN the rule table is applied
- THEN the result is `ArticleType.CIENTIFICO` with confidence `0.83` and
  reasoning text identical to legacy case 5's reasoning string

#### Scenario: Case 9 — near-miss with zero structural support yields DIVULGACION

- GIVEN signals `s2a=False, s2b=False, s3=True, s4=True, s5=True, s6=False`
- WHEN the rule table is applied
- THEN the result is `ArticleType.DIVULGACION` with `confidence=None` and
  reasoning text identical to legacy case 9's reasoning string

#### Scenario: Case 16 — S4 and S5 without S3 yields DIVULGACION, not CIENTIFICO

- GIVEN signals `s2a=False, s2b=False, s3=False, s4=True, s5=True, s6=False`
- WHEN the rule table is applied
- THEN the result is `ArticleType.DIVULGACION` with `confidence=None` —
  absence of `s3` (methodological vocabulary) prevents CIENTIFICO regardless
  of `s4`/`s5` presence

#### Scenario: Case 19 — no signals detected yields OPINION

- GIVEN signals `s2a=False, s2b=False, s3=False, s4=False, s5=False, s6=False`
- WHEN the rule table is applied
- THEN the result is `ArticleType.OPINION` with `confidence=None` and
  reasoning text identical to legacy case 19's reasoning string

#### Scenario: All 19 cases are covered by domain tests

- GIVEN the full domain test suite for the rule table
- WHEN test cases are enumerated
- THEN each of the 19 cases in the table above has at least one test
  asserting its exact `(article_type, confidence, reasoning)` output against
  the legacy implementation's output for equivalent signal inputs

### Requirement: ClassificationConfidence Enum Replaces Inline Confidence Literals

`ClassificationConfidence` (file path finalized in design, e.g.
`src/domain/enums/classification_confidence.py`) MUST be a `float`-mixin enum
(`class ClassificationConfidence(float, Enum)`) with exactly 5 members,
corresponding one-to-one to the 5 distinct confidence literals the legacy
rule table hardcodes (0.95, 0.90, 0.86, 0.85, 0.83). Each member MUST have an
English name (this is a brand-new enum introduced during migration, not a
legacy-carried identifier) and MUST be usable directly as a `float` in
comparisons, arithmetic, and DTO serialization without needing `.value`
access. Every site in the rule table and IMRyD override path that legacy
hardcodes one of these 5 literals MUST use the corresponding enum member
instead of the raw float.

#### Scenario: Enum has exactly 5 members with English names

- GIVEN the `ClassificationConfidence` enum
- WHEN its members are enumerated
- THEN there are exactly 5, with English names, and their float values are
  exactly `{0.95, 0.90, 0.86, 0.85, 0.83}`

#### Scenario: Enum members behave as plain floats

- GIVEN a `ClassificationConfidence` member, e.g. one with value `0.95`
- WHEN it is compared against the float `0.95` or used in arithmetic
- THEN the comparison/arithmetic behaves identically to the raw float `0.95`

#### Scenario: No raw confidence literals remain in the rule table

- GIVEN the file containing the 19-case rule table
- WHEN its source is inspected for the literals `0.95`, `0.90`, `0.86`,
  `0.85`, `0.83`
- THEN none of these appear as bare float literals — each is replaced by the
  corresponding `ClassificationConfidence` enum member

### Requirement: ArticleType Member Names Stay Unchanged

`ArticleType` (`src/domain/enums/article_type.py`) is a pre-existing legacy
identifier and MUST NOT have its member names renamed by this slice. Its
members `CIENTIFICO`, `DIVULGACION`, `OPINION` (and `UNKNOWN`, if present)
MUST keep their current Spanish names and string values.

#### Scenario: ArticleType definition is byte-for-byte unchanged

- GIVEN `src/domain/enums/article_type.py`
- WHEN this slice is applied
- THEN the file's member names and values are identical to their pre-slice
  state

### Requirement: classify_article_size Migrates into article_size.py

The orphaned `classify_article_size(char_count: int) -> ArticleSize` helper
function (currently present only in legacy `domain/enums.py`, never carried
into `src/domain/enums/article_size.py`) MUST be added to
`src/domain/enums/article_size.py`, alongside the existing `ArticleSize`
enum, mirroring how `quality_level.py` carries `get_quality_level_from_score`
as a module-level function alongside its enum. Its threshold logic MUST be
ported verbatim: `36000 <= char_count <= 40000` → `LARGO`;
`16000 <= char_count <= 24000` → `CORTO`; `24001 <= char_count <= 35999` →
`NO_DEFINIDO`; otherwise → `FUERA_RANGO`.

#### Scenario: Each threshold boundary maps to the correct ArticleSize

- GIVEN char counts `16000`, `24000`, `24001`, `35999`, `36000`, `40000`, and
  `40001`
- WHEN `classify_article_size()` is called with each value
- THEN the results are `CORTO`, `CORTO`, `NO_DEFINIDO`, `NO_DEFINIDO`,
  `LARGO`, `LARGO`, `FUERA_RANGO` respectively

#### Scenario: Function lives alongside the ArticleSize enum

- GIVEN `src/domain/enums/article_size.py`
- WHEN the file is inspected after this slice is applied
- THEN it defines both the `ArticleSize` enum and the
  `classify_article_size()` function in the same file

### Requirement: ArticleClassifier Is Consumed Directly by the Orchestrator

> **Superseded (2026-07-04, `refactor_analyze_document_wiring`)**: `ClassifyArticleUseCase`
> and `ClassifyArticleUseCaseWiring` were eliminated as redundant pass-through layers.
> `AnalyzeDocumentUseCase` now depends on `ArticleClassifier` directly and calls
> `.classify(document_content=...)` from its `execute()` method — see
> `openspec/specs/analyze-document/spec.md`. `AnalyzeDocumentUseCaseWiring._get_article_classifier()`
> constructs the domain service directly (no intermediate sub-wiring), and shares one
> `_get_llm_generator()` instance with `QualityAnalyzer` (see analyze-quality spec).

`AnalyzeDocumentUseCase` MUST depend on `ArticleClassifier` directly and call
`classify(document_content=document_content)` without adding business logic.

#### Scenario: Orchestrator uses the domain service's result unchanged

- GIVEN a `DocumentContentDTO`
- WHEN `AnalyzeDocumentUseCase.execute()` calls `self._article_classifier.classify(document_content=document_content)`
- THEN the returned `ClassificationResultDTO` matches what the domain
  service's classification method would produce for the same input

### Requirement: AnalyzeDocumentUseCaseWiring Owns Tunable Defaults

> **Superseded (Phase 3 Laya System 1 integration, TASK-16)**: In Phase 3 Laya System 1
> integration (TASK-16), `ARTICLE_CLASSIFIER_TEMPERATURE` and `ARTICLE_CLASSIFIER_NUM_PREDICT`
> env vars were retired. `ArticleClassifier` no longer depends on `LlmGeneratorPort` or
> generation tunables; S4, S5, and S6 are derived directly from `laya_decision: LayaDecisionResultDTO`.

`AnalyzeDocumentUseCaseWiring._get_article_classifier()` MUST construct `ArticleClassifier`
directly. It MUST reuse the shared `OllamaGeneratorAdapter` instance from `_get_llm_generator()`
(no new adapter introduced) and MUST be the sole place where `ARTICLE_CLASSIFIER_TEMPERATURE` and
`ARTICLE_CLASSIFIER_NUM_PREDICT` are read from the environment (via
`python-dotenv`) and supplied as `temperature`/`num_predict` to
`ArticleClassifier`'s constructor — neither the domain service nor the
adapter MUST contain a default value for either parameter.

#### Scenario: Wiring produces a usable ArticleClassifier instance

- GIVEN an `AnalyzeDocumentUseCaseWiring` instance with the required env vars
  set
- WHEN `create_use_case()` is called
- THEN the resulting `AnalyzeDocumentUseCase._article_classifier` is a real
  `ArticleClassifier` backed by a real `OllamaGeneratorAdapter` and
  constructed with the env-sourced `temperature`/`num_predict` values

#### Scenario: Domain service constructor has no temperature/num_predict defaults

- GIVEN the `ArticleClassifier` constructor signature
- WHEN it is inspected
- THEN neither `temperature` nor `num_predict` has a default value — only
  the wiring supplies values for them

### Requirement: No print() Statements in New Code

None of the new domain, application, or infrastructure files introduced by
this slice MUST contain a `print()` call. The legacy classifier's
exception-path `print()` (in the S4/S5/S6 LLM call's error handler) is
dropped, not replaced with logging, consistent with the `analyze-quality`
precedent.

#### Scenario: No print calls anywhere in the new code

- GIVEN the full set of new files introduced by this slice (signal detector,
  text sampler, response parser, domain service, enum, use case, wiring)
- WHEN their source is inspected
- THEN none contain a `print(` call

## Out of Scope

- `business_logic/structure_analyzer.py` / `business_logic/article_classifier.py`
  — legacy files remain unmodified; coexistence maintained until the
  caller-switchover slice.
- `src/domain/structure/structure_validator.py` — confirmed no overlap beyond
  the naming-collision concern resolved by this slice's rename requirement;
  no code changes.
- `business_logic/article_analyzer.py` — the top-level orchestrator that will
  call `ClassifyArticleUseCase` and the other use cases together; deferred to
  a future slice.
- Any accuracy improvements, rule-table changes, or new classification
  signals — exact behavioral parity with the legacy classifier is this
  slice's goal.
- Wiring `ClassifyArticleUseCase` into `main.py` — deferred to the
  caller-switchover slice.
- Deduplicating the IMRyD signal detector's keyword matching against
  `StructureValidator`'s independent section-alias matching.
- Module-level `analyze_structure()` / `classify_document()` convenience
  functions and `__main__` smoke-test blocks from both legacy files.
