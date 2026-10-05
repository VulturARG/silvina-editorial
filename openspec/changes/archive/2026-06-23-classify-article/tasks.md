# Tasks: classify-article (Slice 6)

> **Context**: Single PR-shaped slice (no PR-A/PR-B split needed — see Review Workload Forecast).
> Migrates `business_logic/structure_analyzer.py` (renamed) and
> `business_logic/article_classifier.py` (4-way split) into the hexagonal architecture, reusing
> `LlmGeneratorPort`/`OllamaGeneratorAdapter` from Slice 5 (`analyze-quality`) via an additive
> `options` parameter. Includes one retrofit of already-merged Slice 5 code
> (`AnalyzeQualityUseCaseWiring._read_prompt_template` deleted in favor of a new shared
> `read_text_resource()` helper, per ADR-8) — this is the only task set in this slice that touches
> a previously-merged, currently-live file, and is explicitly gated by its own regression task
> (T-26). Strict TDD RED→GREEN per unit, same conventions as Slice 5 PR-A/PR-B: one `TestCase`
> class per test file, `setUp()`/`setUpClass()` for shared fixtures, verbatim-port tasks call out
> exact legacy line ranges to diff against.

---

## Phase 0 — `ImrydSignalDetector` (renamed, verbatim port)

### [x] T-01: RED — write `ImrydSignalDetector` tests
- File: `src/domain/tests/classification/test_imryd_signal_detector.py` — new file (create
  `src/domain/tests/classification/__init__.py` alongside it).
- `test_long_body_paragraph_is_never_treated_as_section_header` — paragraph > 5 words containing
  "introducción"/"results" inside body prose; assert it does not set any `has_*` signal.
- `test_all_four_core_sections_present_yields_imryd_complete_true` — short header paragraphs for
  introduction/methods/results/discussion, no conclusion header; assert those 4 signals `True`,
  `has_conclusion` `False`, `imryd_complete` `True`.
- `test_conclusion_alone_does_not_satisfy_imryd_complete` — conclusion header only; assert
  `has_conclusion=True`, `imryd_complete=False`.
- `test_bilingual_keyword_matching_covers_spanish_and_english_variants` — Spanish headers
  ("Metodología", "Resultados", "Discusión"); assert `has_methods`/`has_results`/`has_discussion`
  all `True`, matching an equivalent English-header document.
- **Satisfies**: Requirement "IMRyD Signal Detector — Deterministic Section-Keyword Presence"
  (all 4 scenarios) and Requirement "Naming Collision Avoidance with StructureValidator" (class
  naming half — verified structurally here by class name, completeness in T-35).
- **Parallel/Sequential**: Parallel with T-03, T-05, T-07 (independent files). Sequential RED
  before T-02 GREEN.

### [x] T-02: GREEN — implement `ImrydSignalDetector`
- File: `src/domain/classification/imryd_signal_detector.py` — exact code from design.md, ported
  verbatim from `business_logic/structure_analyzer.py`'s `StructureAnalyzer.analyze()`: same
  `IMRYD_KEYWORDS` table (bilingual), same ≤5-word header-candidate filter, same 6-key signal
  dict, same `imryd_complete` semantics (intro+methods+results+discussion required, conclusion
  excluded from the AND). `IMRYD_KEYWORDS` becomes a private module constant
  (`_IMRYD_KEYWORDS`), not a public class attribute. No constructor. Method named `detect()`, not
  `analyze()`.
- **Satisfies**: same requirements as T-01.
- **Parallel/Sequential**: Sequential after T-01.

---

## Phase 1 — `ClassificationConfidence` enum

### [x] T-03: RED — write `ClassificationConfidence` test
- File: `src/domain/tests/enums/test_classification_confidence.py`.
- `test_enum_has_exactly_five_members_with_english_names` — `len(ClassificationConfidence) == 5`;
  member names are English identifiers (`IMRYD_OVERRIDE`, `FULL_SIGNAL_MATCH`,
  `RECENT_BIBLIOGRAPHY_SUPPORT`, `COMPLETE_BIBLIOGRAPHY_SUPPORT`, `SUFFICIENT_REFERENCE_COUNT`);
  float values are exactly `{0.95, 0.90, 0.86, 0.85, 0.83}`.
- `test_enum_members_behave_as_plain_floats` — `ClassificationConfidence.IMRYD_OVERRIDE == 0.95`,
  and arithmetic (`ClassificationConfidence.IMRYD_OVERRIDE * 2 == 1.90`) behaves identically to
  the raw float.
- **Satisfies**: Requirement "ClassificationConfidence Enum Replaces Inline Confidence Literals"
  (first 2 scenarios — "no raw literals remain" scenario verified later in T-36).
- **Parallel/Sequential**: Parallel with T-01, T-05, T-07. Sequential RED before T-04 GREEN.

### [x] T-04: GREEN — implement `ClassificationConfidence`
- File: `src/domain/enums/classification_confidence.py` — exact code from design.md (ADR-3):
  `class ClassificationConfidence(float, Enum)` with the 5 members and values listed above.
- **Satisfies**: same requirement.
- **Parallel/Sequential**: Sequential after T-03.

---

## Phase 2 — `classify_article_size()` migration

### [x] T-05: RED — write `classify_article_size()` test
- File: `src/domain/tests/enums/test_classify_article_size.py` — new file (separate from any
  existing `ArticleSize` enum test file, per analyze-quality's `get_quality_level_from_score`
  precedent of a dedicated function test file).
- `test_each_threshold_boundary_maps_to_correct_article_size` — parametrized/explicit cases for
  char counts `16000, 24000, 24001, 35999, 36000, 40000, 40001` → `CORTO, CORTO, NO_DEFINIDO,
  NO_DEFINIDO, LARGO, LARGO, FUERA_RANGO` respectively.
- **Satisfies**: Requirement "classify_article_size Migrates into article_size.py" (boundary
  scenario — co-location scenario verified in T-06 by file inspection).
- **Parallel/Sequential**: Parallel with T-01, T-03, T-07. Sequential RED before T-06 GREEN.

### [x] T-06: GREEN — implement `classify_article_size()`
- File: `src/domain/enums/article_size.py` — append function alongside the existing `ArticleSize`
  enum (do not create a new file; do not touch existing `ArticleSize` member definitions). Ported
  verbatim from legacy `domain/enums.py`, with the `if/elif/elif/else` chain reformatted as
  early-return guard clauses: `36000 <= char_count <= 40000` → `LARGO`;
  `16000 <= char_count <= 24000` → `CORTO`; `24001 <= char_count <= 35999` → `NO_DEFINIDO`;
  otherwise → `FUERA_RANGO`.
- After this task, confirm via `Read` that `article_size.py` defines both `ArticleSize` and
  `classify_article_size` in the same file (co-location scenario).
- **Satisfies**: same requirement (both scenarios).
- **Parallel/Sequential**: Sequential after T-05.

---

## Phase 3 — `ArticleClassificationTextSampler` (new file, ported logic)

### [x] T-07: RED — write `ArticleClassificationTextSampler` tests
- File: `src/domain/tests/classification/test_article_classification_text_sampler.py`.
- `test_bibliography_section_is_excluded_from_the_sample` — paragraphs include a short standalone
  "Referencias" header followed by bibliography entries; assert none of the post-marker text
  appears in the built sample.
- `test_sample_combines_intro_and_ending_segments` — bibliography-excluded text exceeds 6000
  characters; assert result equals first 3500 chars concatenated with last 2500 chars of the
  bibliography-excluded text.
- `test_empty_sample_falls_back_to_first_six_thousand_characters_of_full_text` — bibliography
  exclusion reduces text to empty string; assert result is first 6000 chars of the full joined
  text (bibliography included).
- **Satisfies**: Requirement "Dedicated Classification Text Sampler" (all 3 scenarios).
- **Parallel/Sequential**: Parallel with T-01, T-03, T-05. Sequential RED before T-08 GREEN.

### [x] T-08: GREEN — implement `ArticleClassificationTextSampler`
- File: `src/domain/classification/article_classification_text_sampler.py` — exact code from
  design.md, ported verbatim from legacy `_build_text_sample()`: module constants
  `_INTRODUCTION_CHARACTER_LIMIT=3500`, `_CONCLUSION_CHARACTER_LIMIT=2500`,
  `_FALLBACK_CHARACTER_LIMIT=6000`, `_BIBLIOGRAPHY_HEADER_MAX_LENGTH=30`,
  `_BIBLIOGRAPHY_MARKERS` tuple. No constructor params (diverges intentionally from
  `QualityTextSampler`'s tunable-constructor pattern — confirmed in design ADR notes, no `.env`
  exposure requested for these 2 constants).
- **Satisfies**: same requirement.
- **Parallel/Sequential**: Sequential after T-07.

---

## Phase 4 — `ArticleClassificationResponseParser` (new file, ported logic)

### [x] T-09: RED — write `ArticleClassificationResponseParser` tests
- File: `src/domain/tests/classification/test_article_classification_response_parser.py`.
- `test_well_formed_response_parses_all_three_signals_correctly` — response containing
  `S4: SI`, `S5: NO`, `S6: SI`; assert `parser.parse(text) == (True, False, True)`.
- `test_malformed_response_yields_all_false_without_raising` — response containing none of the
  expected markers; assert `(False, False, False)` with no exception raised.
- **Satisfies**: Requirement "S4/S5/S6 Response Parser" (both scenarios).
- **Parallel/Sequential**: Parallel with Phase 0-3's RED tasks. Sequential RED before T-10 GREEN.

### [x] T-10: GREEN — implement `ArticleClassificationResponseParser`
- File: `src/domain/classification/article_classification_response_parser.py` — exact code from
  design.md: 3 compiled case-insensitive-via-uppercase regex patterns
  (`S4\s*:\s*SI`, `S5\s*:\s*SI`, `S6\s*:\s*SI`), `parse()` returns bare
  `tuple[bool, bool, bool]` (no DTO/NamedTuple wrapper — 3 unrelated booleans, no grouping key).
- **Satisfies**: same requirement.
- **Parallel/Sequential**: Sequential after T-09.

---

## Phase 5 — `LlmGeneratorPort` / `OllamaGeneratorAdapter` additive `options` param

### [x] T-11: RED — extend `OllamaGeneratorAdapter` test with options-forwarding cases
- File: `src/infrastructure/tests/test_ollama_generator_adapter.py` — MODIFY existing file (do not
  overwrite the 2 existing test methods from Slice 5).
- Add `test_generate_forwards_options_dict_to_ollama_generate` — mock `ollama.generate`, call
  `adapter.generate("prompt", options={"temperature": 0.1, "num_predict": 300})`, assert the mock
  was called with `options={"temperature": 0.1, "num_predict": 300}`.
- Add `test_generate_without_options_argument_preserves_prior_behavior` — call
  `adapter.generate("prompt")` with no `options` argument; assert the mock's `options` kwarg is
  `None` (no non-`None` default silently injected), and confirm both pre-existing Slice 5 tests
  (`test_generate_returns_stripped_response_text`,
  `test_generate_raises_language_model_unavailable_on_backend_failure`) still pass unmodified.
- **Satisfies**: Requirement "LlmGeneratorPort Gains an Additive Options Parameter" (options-
  forwarding scenario + omission-preserves-behavior scenario).
- **Parallel/Sequential**: Parallel with Phase 0-4. Sequential RED before T-12 GREEN.

### [x] T-12: GREEN — extend `LlmGeneratorPort` and `OllamaGeneratorAdapter` signatures
- File: `src/domain/ports/llm_generator_port.py` — change `generate(self, prompt: str) -> str` to
  `generate(self, prompt: str, options: dict | None = None) -> str`.
- File: `src/infrastructure/adapters/llm_generator/ollama_generator_adapter.py` — change
  `generate(self, prompt: str) -> str` to
  `generate(self, prompt: str, options: dict | None = None) -> str`; forward `options` to
  `ollama.generate(model=..., prompt=..., options=options)` unmodified, with no adapter-side
  interpretation/defaulting/translation. Diff against the actual current file (not Slice 5's own
  design-doc snapshot, which has a wider `except` clause than the real source) when applying this
  change — preserve the existing narrower `except` clause exactly.
- Run `python -m pytest src/domain/tests/quality/ src/infrastructure/tests/test_ollama_generator_adapter.py src/application/tests/test_analyze_quality_use_case.py -q` after this task — confirm
  `analyze-quality`'s existing call site (`self._llm_generator.generate(prompt)`, no `options`
  argument) still compiles and passes with zero changes to `quality_analyzer.py` or its tests.
- **Satisfies**: Requirement "LlmGeneratorPort Gains an Additive Options Parameter" (all 3
  scenarios, including "existing analyze-quality call site is unaffected").
- **Parallel/Sequential**: Sequential after T-11.

---

## Phase 6 — Shared `read_text_resource()` helper + `AnalyzeQualityUseCaseWiring` retrofit

> **Risk note**: this phase modifies already-merged, currently-live Slice 5 code
> (`AnalyzeQualityUseCaseWiring`). T-15 is a mandatory, explicit regression gate for this reason —
> do not skip it even though the retrofit is designed to be behavior-invisible.

### [x] T-13: RED — write `read_text_resource()` test
- File: `src/infrastructure/tests/test_text_resource_loader.py` — new file.
- `test_reads_utf8_text_resource_file` — write a temp UTF-8 `.txt` fixture (or use an existing
  resource file, e.g. one of the quality prompt `.txt` files, as a known-content fixture), call
  `read_text_resource(directory, filename)`, assert returned string matches file content exactly.
- **Satisfies**: ADR-8's shared-helper extraction (no spec requirement directly names this helper
  — it is a design-level refactor satisfying the "Updated Dependencies" implication of the
  `ClassifyArticleUseCaseWiring` requirement, by providing the file-reading mechanism it needs).
- **Parallel/Sequential**: Parallel with Phase 0-5. Sequential RED before T-14 GREEN.

### [x] T-14: GREEN — implement `read_text_resource()` and retrofit `AnalyzeQualityUseCaseWiring`
- File: `src/infrastructure/resources/text_resource_loader.py` — exact code from design.md (ADR-8):
  `def read_text_resource(directory: str, filename: str) -> str:` using
  `Path(join(directory, filename)).read_text(encoding="utf-8")`.
- File: `src/infrastructure/wirings/analyze_quality_use_case_wiring.py` — MODIFY: delete the
  private `_read_prompt_template` method entirely; replace its 2 call sites
  (`clarity_coherence_prompt_template=...`, `argumentation_conclusions_prompt_template=...`) with
  direct calls to `read_text_resource(PROMPTS_DIR, "clarity_coherence_prompt.txt")` and
  `read_text_resource(PROMPTS_DIR, "argumentation_conclusions_prompt.txt")`; add the import
  `from src.infrastructure.resources.text_resource_loader import read_text_resource`. Remove the
  now-unused `from os.path import join` / `from pathlib import Path` imports if nothing else in
  the file uses them after the method's deletion (confirm via `Read` before removing).
- **Satisfies**: ADR-8 retrofit.
- **Parallel/Sequential**: Sequential after T-13.

### [x] T-15: MANDATORY regression gate — re-run analyze-quality's existing test suite after retrofit
- Run `python -m pytest src/infrastructure/tests/test_analyze_quality_use_case_wiring.py -v` —
  confirm both pre-existing tests
  (`test_create_use_case_returns_correct_type`, `test_llm_generator_accessor_returns_port_type`)
  still pass unmodified (neither test directly exercised `_read_prompt_template`, per design's
  confirmed-zero-coverage note, so this run should be a clean pass with no test changes needed).
- Run the FULL regression suite: `python -m pytest src/ -q` — confirm zero regressions against
  the pre-retrofit baseline (PR-B's 284 passed plus this slice's new tests accumulated so far).
  This is a non-skippable checkpoint specifically because this phase touches a previously-merged,
  currently-live PR's wiring file — do not proceed to Phase 7+ until this passes.
- **Satisfies**: housekeeping/safety gate for ADR-8's retrofit — not requirement-specific, but
  blocks all downstream work until the merged Slice 5 surface is confirmed unbroken.
- **Parallel/Sequential**: Sequential after T-14. Blocks Phase 7 onward.

---

## Phase 7 — Prompt template file (no test; static text)

### [x] T-16: Create `s4_s5_s6_signal_prompt.txt` and `prompts/classification/__init__.py`
- `../../../../src/infrastructure/resources/prompts/classification/s4_s5_s6_signal_prompt.txt` — exact Spanish
  text from design.md, copied verbatim from legacy's S4/S5/S6 f-string body, with `{title}` and
  `{text_sample}` retained as literal `.format()`-style placeholders (2 placeholders, vs.
  analyze-quality's 1).
- `src/infrastructure/resources/prompts/classification/__init__.py` — identical pattern to
  `prompts/quality/__init__.py`: `from os import path; PROMPTS_DIR = path.dirname(__file__)`.
- No test file for the `.txt` content itself — verified indirectly by T-18's rendered-prompt
  test (literal string comparison, same convention as Slice 5's T-11/T-14 pairing).
- **Satisfies**: prerequisite for `ArticleClassifier`'s LLM-call requirement and
  `ClassifyArticleUseCaseWiring`'s requirement (file existence half).
- **Parallel/Sequential**: Parallel with Phase 0-6 (fully independent files).

---

## Phase 8 — `_ClassificationSignals` dataclass + `_RuleCase`/`_RULE_TABLE` + `ArticleClassifier`

> **Highest-risk transcription unit.** Broken into fine-grained tasks per rule-table row group,
> matching the design's case grouping (IMRyD override / CIENTIFICO 2-5 / DIVULGACION near-miss
> 6-9 / DIVULGACION standard 10-18 / OPINION 19) and the 5 separate test files the design
> specifies. Each GREEN task for the rule table must diff its ported rows character-for-character
> against `business_logic/article_classifier.py`'s `_apply_rule` method — zero design decisions
> remain at this point (ADR-3/6/7 already resolved every behavior-relevant choice); this is pure,
> verified transcription.

### [x] T-17: RED — write `fake_llm_generator_port.py` test double
- File: `src/domain/tests/classification/fake_llm_generator_port.py` — mirrors
  `src/domain/tests/quality/fake_llm_generator_port.py`'s shape exactly: records `generate()`
  call arguments (including `options`), returns a configurable canned response.
- Not itself a `TestCase` — the one established non-`TestCase` exception per design's "Test File
  Layout" section.
- **Satisfies**: test infrastructure prerequisite for T-18 onward (no direct spec requirement —
  enables the "fake port records call arguments" scenario under "ArticleClassifier Domain Service
  Orchestrates Classification").
- **Parallel/Sequential**: Parallel with Phase 0-7. Must exist before T-19's RED.

### [x] T-18: RED — write `_ClassificationSignals` + reference/vocabulary signal tests
- File: `src/domain/tests/classification/test_article_classifier_signals.py` — new file, tests
  the 3 pure signal-detection methods directly (not via full `classify()`), using a minimal
  `ArticleClassifier` construction with the fake port from T-17.
- `test_reference_count_signal_fires_at_exactly_twelve_references` — 12 references; assert `True`.
- `test_reference_count_signal_does_not_fire_at_eleven_references` — 11 references; assert
  `False`.
- `test_reference_recency_signal_uses_maximum_year_per_reference` — a reference containing both
  "1998" and "2024"; assert it is treated as year `2024`, not `1998`.
- `test_no_references_yields_false_for_both_reference_signals` — empty references list; assert
  both `False`.
- `test_four_general_terms_with_one_hard_term_satisfies_methodological_vocabulary_signal` — 4
  distinct vocab terms, ≥1 a hard term (e.g. "análisis estadístico"); assert `True`.
- `test_four_general_terms_with_zero_hard_terms_does_not_satisfy_signal` — 4 distinct vocab
  terms, zero hard terms; assert `False`.
- `test_accent_insensitive_matching_treats_accented_and_unaccented_terms_identically` —
  "metodologia" (unaccented) document text vs. "metodología" (accented) vocabulary entry; assert
  match regardless of accent.
- **Satisfies**: Requirement "Reference-Count and Reference-Recency Signals Are Ported Verbatim"
  (all 4 scenarios) and Requirement "Methodological Vocabulary Signal Is Ported Verbatim" (all 3
  scenarios).
- **Parallel/Sequential**: Parallel with T-20, T-22, T-24, T-26's RED (different test files, same
  target module — write RED first, hold GREEN until T-19/T-21/T-23/T-25/T-27 land together since
  they share one file). Depends on T-04 (`ClassificationConfidence`), T-17 (fake port) existing.

### [x] T-19: GREEN — implement `_ClassificationSignals` dataclass + reference/vocabulary signal
methods on `ArticleClassifier`
- File: `src/domain/classification/article_classifier.py` — create the file with: module
  constants `_METHODOLOGICAL_VOCABULARY` (~70 terms) and `_HARD_METHODOLOGICAL_TERMS` (~30 terms,
  `frozenset`), copied character-for-character from
  `business_logic/article_classifier.py` lines 15-55 (literal copy-paste with diff-against-source
  verification — not re-transcription); `_MINIMUM_REFERENCE_COUNT=12`,
  `_RECENT_REFERENCE_YEAR_OFFSET=4`, `_MINIMUM_RECENT_REFERENCE_RATIO=0.5`,
  `_MINIMUM_VOCABULARY_TERM_COUNT=4`, `_MINIMUM_HARD_TERM_COUNT=1`; the `_ClassificationSignals`
  frozen dataclass (ADR-7, 6 named `has_*` boolean fields); `ArticleClassifier.__init__` accepting
  the 7 documented constructor params (`llm_generator`, `signal_detector`, `text_sampler`,
  `response_parser`, `signal_prompt_template`, `temperature`, `num_predict` — none defaulted);
  `_detect_sufficient_reference_count`, `_detect_recent_reference_majority`,
  `_detect_methodological_vocabulary` methods, ported verbatim from legacy
  `_signal_reference_count`/`_signal_reference_recency`/`_signal_methodological_vocab` with the
  renamed verb+condition method names (per design's explicit rename list — avoids leaking s2a/s2b/
  s3 shorthand into method names).
- Do NOT implement `classify()` or `_apply_rule` yet — those land in T-23/T-25/T-27/T-29/T-31.
- **Satisfies**: same requirements as T-18, plus partial groundwork for "Constructor requires
  temperature and num_predict with no defaults" and "Domain service has zero infrastructure
  imports" scenarios (fully verified later in T-33/T-34).
- **Parallel/Sequential**: Sequential after T-18 (and T-04, T-17).

### [x] T-20: RED — write IMRyD override + LLM-call-options tests on `ArticleClassifier`
- File: `src/domain/tests/classification/test_article_classifier_imryd_override.py` — case 1.
- `test_imryd_override_short_circuits_remaining_five_signals` — fake `ImrydSignalDetector`-like
  double (or real `ImrydSignalDetector` with input crafted to set `imryd_complete=True`) plus
  `ArticleSize` not `FUERA_RANGO`; assert result is `ArticleType.CIENTIFICO` with confidence
  `ClassificationConfidence.IMRYD_OVERRIDE` (0.95), and that the fake port's `generate()` was
  never called (proves the remaining 5 signals, including the LLM call, were never computed).
- `test_imryd_complete_but_article_size_out_of_range_does_not_override` — `imryd_complete=True`
  but `ArticleSize.FUERA_RANGO`; assert override does NOT apply and classification proceeds to
  compute the remaining 5 signals (assert fake port's `generate()` WAS called this time).
- `test_llm_call_passes_temperature_and_num_predict_as_options` — `ArticleClassifier` constructed
  with `temperature=0.1, num_predict=300`; assert fake port recorded
  `generate(..., options={"temperature": 0.1, "num_predict": 300})` at the S4/S5/S6 call site.
- `test_constructor_without_temperature_or_num_predict_raises_type_error` — attempt construction
  omitting either parameter; assert `TypeError`.
- `test_domain_service_has_zero_infrastructure_imports` — inspect
  `article_classifier.py`'s import statements; assert none import from `src/infrastructure/` or
  `ollama`.
- **Satisfies**: Requirement "ArticleClassifier Domain Service Orchestrates Classification" (all
  4 scenarios).
- **Parallel/Sequential**: Parallel with T-18 (different test file). Depends on T-19 existing
  (constructor + signal methods) for GREEN; RED can be written referencing not-yet-existing
  `classify()` per standard TDD.

### [x] T-21: GREEN — implement `classify()` entry point + IMRyD override branch
- File: `src/domain/classification/article_classifier.py` — MODIFY: add `classify(document_content)
  -> ClassificationResultDTO`: raise `ClassificationFailed()` if `document_content.paragraphs` is
  empty; compute `article_size` via `classify_article_size()`; compute `imryd_signals` via
  `self._signal_detector.detect(document_content)`; if `imryd_signals["imryd_complete"]` and
  `article_size != ArticleSize.FUERA_RANGO`, short-circuit and return
  `ClassificationResultDTO.create(article_type=ArticleType.CIENTIFICO, article_size=article_size,
  confidence=ClassificationConfidence.IMRYD_OVERRIDE, reasoning="Estructura IMRyD completa
  detectada (override determinístico).")` without computing any other signal. Otherwise, proceed
  to build the text sample, call `_detect_research_intent_signals` (the LLM call, passing
  `options={"temperature": self._temperature, "num_predict": self._num_predict}`), assemble
  `_ClassificationSignals`, and call `self._apply_rule(signals, article_size)` — `_apply_rule`
  itself is stubbed/raises `NotImplementedError` for now (implemented starting T-23).
- **Satisfies**: same requirements as T-20 (the IMRyD-override and LLM-options scenarios only —
  full rule-table application verified once `_apply_rule` lands).
- **Parallel/Sequential**: Sequential after T-19, T-20.

### [x] T-22: RED — write CIENTIFICO cases 2-5 tests
- File: `src/domain/tests/classification/test_article_classifier_cientifico.py`.
- `test_case_2_full_signal_set_produces_zero_point_nine_confidence` — signals
  `s2a=True, s2b=True, s3=True, s4=True, s5=True, s6=True`; assert
  `ArticleType.CIENTIFICO`, confidence `0.90`, reasoning matches legacy case 2's exact string.
- `test_case_3_missing_s2a_produces_zero_point_eight_six_confidence` — `s2a=False` else same as
  case 2; assert confidence `0.86`, reasoning matches legacy case 3.
- `test_case_4_missing_s6_produces_zero_point_eight_five_confidence` — `s6=False`, `s2a=True,
  s2b=True`; assert confidence `0.85`, reasoning matches legacy case 4.
- `test_case_5_missing_s2b_produces_zero_point_eight_three_confidence` (minimum-threshold
  CIENTIFICO) — `s2a=True, s2b=False, s3=True, s4=True, s5=True, s6=True`; assert confidence
  `0.83`, reasoning matches legacy case 5.
- For each test, drive signals via constructing the document/fake-port inputs needed to produce
  the target `_ClassificationSignals` values (not by injecting the dataclass directly, unless the
  design's test layout explicitly permits constructing `_ClassificationSignals` directly for
  rule-table-focused tests — confirm via T-19's class visibility; if `_ClassificationSignals` is
  importable from the test file, prefer direct dataclass construction for precision and speed).
- **Satisfies**: Requirement "19-Case Rule Table Produces Identical Output to Legacy" (case 2 and
  case 5 scenarios explicitly, cases 3-4 as additional coverage toward "all 19 cases" scenario).
- **Parallel/Sequential**: Parallel with T-24, T-26, T-28 (different test files). Sequential RED
  before T-23 GREEN.

### [x] T-23: GREEN — implement `_RuleCase`/`_RULE_TABLE` rows for CIENTIFICO (cases 2-5) +
`_apply_rule` dispatch loop skeleton
- File: `src/domain/classification/article_classifier.py` — MODIFY: add `_RuleCase` frozen
  dataclass (`predicate`, `article_type`, `confidence`, `reasoning` callable); `_FULL_CORE` lambda
  helper; the 4 CIENTIFICO `_RuleCase` rows (cases 2-5) exactly as specified in design ADR-6,
  each paired with its own module-level `_reasoning_case_N` function returning the unmodified
  legacy Spanish reasoning string (diff-verified character-for-character against
  `business_logic/article_classifier.py` lines 279-541); implement `_apply_rule`'s dispatch loop
  (`for case in _RULE_TABLE: if case.predicate(signals): return ...`) — `_RULE_TABLE` at this
  point contains only the 4 CIENTIFICO rows; the loop's fallback (OPINION) is added in T-29, so
  for now let it raise `NotImplementedError` if no row matches (temporary, replaced in T-29).
- **Satisfies**: same requirement as T-22 (cases 2-5 portion).
- **Parallel/Sequential**: Sequential after T-21, T-22.

### [x] T-24: RED — write DIVULGACION near-miss cases 6-9 tests
- File: `src/domain/tests/classification/test_article_classifier_divulgacion_near_miss.py`.
- `test_case_6_full_core_with_theoretical_justification_only` — `s3∧s4∧s5∧s6`, none of cases 2-5
  matched (i.e. `s2a=False, s2b=False`); assert `ArticleType.DIVULGACION`, `confidence=None`,
  reasoning matches legacy case 6.
- `test_case_7_full_core_with_recent_references_only` — `s3∧s4∧s5∧s2b`, `s2a=False, s6=False`;
  assert DIVULGACION, `confidence=None`, reasoning matches legacy case 7.
- `test_case_8_full_core_with_reference_count_only` — `s3∧s4∧s5∧s2a`, `s2b=False, s6=False`;
  assert DIVULGACION, `confidence=None`, reasoning matches legacy case 8.
- `test_case_9_near_miss_with_zero_structural_support_yields_divulgacion` — signals
  `s2a=False, s2b=False, s3=True, s4=True, s5=True, s6=False`; assert DIVULGACION,
  `confidence=None`, reasoning matches legacy case 9 exactly.
- **Satisfies**: Requirement "19-Case Rule Table Produces Identical Output to Legacy" (case 9
  scenario explicitly; 6-8 as additional "all 19 cases" coverage).
- **Parallel/Sequential**: Parallel with T-22, T-26, T-28. Sequential RED before T-25 GREEN.

### [x] T-25: GREEN — implement `_RULE_TABLE` rows for DIVULGACION near-miss (cases 6-9)
- File: `src/domain/classification/article_classifier.py` — MODIFY: append the 4 near-miss
  `_RuleCase` rows (cases 6-9) to `_RULE_TABLE`, each `_FULL_CORE(s) and <extra condition>`
  predicate per design ADR-6's exact lambda definitions, paired with `_reasoning_case_6` through
  `_reasoning_case_9` functions (verbatim legacy strings, diff-verified).
- **Satisfies**: same requirement as T-24.
- **Parallel/Sequential**: Sequential after T-23, T-24.

### [x] T-26: RED — write DIVULGACION standard cases 10-18 tests
- File: `src/domain/tests/classification/test_article_classifier_divulgacion_standard.py`.
- One test per case 10-18, each asserting `ArticleType.DIVULGACION`, `confidence=None`, and
  reasoning matching the corresponding legacy `_reasoning_case_N` string exactly:
  - `test_case_10_s3_and_s4_not_full_branch`
  - `test_case_11_s3_and_s5_not_full_branch_not_case_10`
  - `test_case_12_s3_and_s2a_and_s2b`
  - `test_case_13_s3_and_s2a_only`
  - `test_case_14_s3_and_s2b_only`
  - `test_case_15_s3_only`
  - `test_case_16_s4_and_s5_without_s3_yields_divulgacion_not_cientifico` — signals
    `s2a=False, s2b=False, s3=False, s4=True, s5=True, s6=False`; explicitly assert DIVULGACION
    (NOT CIENTIFICO) — this is the spec's flagged "methodological vocabulary is a mandatory gate"
    scenario; absence of `s3` must block CIENTIFICO regardless of `s4`/`s5`.
  - `test_case_17_s4_only_not_s3_not_s5`
  - `test_case_18_s5_only_not_s3_not_s4`
- **Satisfies**: Requirement "19-Case Rule Table Produces Identical Output to Legacy" (case 16
  scenario explicitly; 10-15/17-18 as "all 19 cases" coverage).
- **Parallel/Sequential**: Parallel with T-22, T-24, T-28. Sequential RED before T-27 GREEN.

### [x] T-27: GREEN — implement `_RULE_TABLE` rows for DIVULGACION standard (cases 10-18)
- File: `src/domain/classification/article_classifier.py` — MODIFY: append the 9 standard
  DIVULGACION `_RuleCase` rows (cases 10-18) to `_RULE_TABLE`, exact predicates per design ADR-6
  (note: cases 10/11 do NOT use `_FULL_CORE` — they test `s3∧s4` and `s3∧s5` individually, which
  is structurally distinct from the full-core near-miss cases 6-9; preserve this distinction
  exactly, do not accidentally reuse `_FULL_CORE` here), paired with `_reasoning_case_10` through
  `_reasoning_case_18` functions (verbatim legacy strings, diff-verified). Row order in the tuple
  must exactly match legacy's branch-check order (cases 10→18 in sequence) — this is what makes
  the first-match loop reproduce legacy's first-match-wins semantics, especially load-bearing for
  case 16 (verify case 16's row sits after cases 10/11's `s3∧s4`/`s3∧s5` rows but is reachable
  when `s3=False`, per the design's documented evaluation order).
- **Satisfies**: same requirement as T-26.
- **Parallel/Sequential**: Sequential after T-25, T-26.

### [x] T-28: RED — write OPINION case 19 test + "all 19 cases" coverage audit test
- File: `src/domain/tests/classification/test_article_classifier_opinion.py`.
- `test_case_19_no_signals_detected_yields_opinion` — signals
  `s2a=False, s2b=False, s3=False, s4=False, s5=False, s6=False`; assert
  `ArticleType.OPINION`, `confidence=None`, reasoning matches legacy case 19 exactly.
- `test_rule_table_has_exactly_eighteen_rows` — `len(_RULE_TABLE) == 18` (case 19 is the loop
  fallback, not a table row — per design ADR-6's explicit "not a table entry" decision).
- `test_all_nineteen_cases_are_covered_by_domain_tests` — audit task: confirm, by inspection of
  this slice's full test suite (T-18 through T-28), every one of the 19 cases in the spec's case
  table has at least one test asserting its exact `(article_type, confidence, reasoning)` output.
  Produce this as an explicit checklist in the PR description or a scratch note (not a new repo
  file), mirroring Slice 5 PR-A's T-16 redistribution-tracking convention.
- **Satisfies**: Requirement "19-Case Rule Table Produces Identical Output to Legacy" (case 19
  scenario + "all 19 cases are covered" scenario).
- **Parallel/Sequential**: Parallel with T-22, T-24, T-26. Sequential RED before T-29 GREEN.

### [x] T-29: GREEN — implement OPINION fallback, finalize `_apply_rule`/`classify()` wiring
- File: `src/domain/classification/article_classifier.py` — MODIFY: replace `_apply_rule`'s
  temporary `NotImplementedError` fallback (from T-23) with the real OPINION fallback path: when
  the loop exhausts `_RULE_TABLE` with no match, return
  `ClassificationResultDTO.create(article_type=ArticleType.OPINION, article_size=article_size,
  confidence=None, reasoning=_reasoning_case_19(signals, active, inactive))`. Confirm
  `_RULE_TABLE` now has exactly 18 rows (cases 2-18) and case 19 is purely the post-loop
  fallback — not appended as a synthetic always-True 19th row.
- **Satisfies**: same requirement as T-28.
- **Parallel/Sequential**: Sequential after T-27, T-28.

---

## Phase 9 — `ClassificationFailed` empty-paragraphs validation test

### [x] T-30: RED+GREEN — write and verify empty-paragraphs validation test
- File: add to `src/domain/tests/classification/test_article_classifier_imryd_override.py` (or a
  new small test method in an existing classification test file — no new file needed for one
  test): `test_empty_paragraphs_raises_classification_failed` — construct `document_content` with
  `paragraphs=[]`; assert `classifier.classify(document_content)` raises `ClassificationFailed`
  (already exists at `src/domain/exceptions/classification_errors.py`, unmodified — confirm no
  duplicate is created).
- This validation path was already implemented in T-21's `classify()` GREEN (the guard clause at
  the top); this task is the explicit RED/confirmation step for that specific behavior, called out
  separately per design ADR-5's exception-strategy decision.
- **Satisfies**: ADR-5's exception-strategy decision (no direct spec scenario names this case
  explicitly, but it underlies the "Domain service has zero infrastructure imports" and general
  robustness expectations of "ArticleClassifier Domain Service Orchestrates Classification").
- **Parallel/Sequential**: Sequential after T-21 (validates already-implemented behavior).

---

## Phase 10 — `ClassifyArticleUseCase`

### [x] T-31: RED — write `ClassifyArticleUseCase` test
- File: `src/application/tests/test_classify_article_use_case.py` — one `TestCase` class,
  `setUp()` instantiates `ClassifyArticleUseCase(classifier=ArticleClassifier(...))` with real
  collaborators (mirrors `test_analyze_quality_use_case.py`'s pattern from Slice 5 PR-B).
- `test_execute_returns_domain_service_result_unchanged` — call
  `use_case.execute(document_content)`, assert result equals
  `classifier.classify(document_content)` called directly with the same input.
- **Satisfies**: Requirement "ClassifyArticleUseCase Thin Pass-Through" (the one scenario).
- **Parallel/Sequential**: Parallel with Phase 7 (T-16), Phase 11's RED. Sequential RED before
  T-32 GREEN. Depends on Phase 8 (`ArticleClassifier`) being fully GREEN.

### [x] T-32: GREEN — implement `ClassifyArticleUseCase`
- File: `src/application/classify_article_use_case.py` — exact code from design.md: constructor
  takes `classifier: ArticleClassifier`, `execute(document_content)` is a one-line delegation to
  `self._classifier.classify(document_content)`. No `article_type` parameter (classification
  produces `ArticleType`, doesn't consume one).
- **Satisfies**: same requirement.
- **Parallel/Sequential**: Sequential after T-31.

---

## Phase 11 — `ClassifyArticleUseCaseWiring`

### [x] T-33: RED — write `ClassifyArticleUseCaseWiring` tests
- File: `src/infrastructure/tests/test_classify_article_use_case_wiring.py` — one `TestCase`
  class, `setUp()` instantiates `self.wiring = ClassifyArticleUseCaseWiring()` (mirrors
  `test_analyze_quality_use_case_wiring.py`'s pattern).
- `test_create_use_case_returns_correct_type` — assert
  `isinstance(wiring.create_use_case(), ClassifyArticleUseCase)`.
- `test_domain_service_constructor_has_no_temperature_or_num_predict_defaults` — inspect
  `ArticleClassifier.__init__`'s signature (e.g. via `inspect.signature`); assert neither
  `temperature` nor `num_predict` has a default value.
- **Satisfies**: Requirement "ClassifyArticleUseCaseWiring Owns Tunable Defaults" (both
  scenarios).
- **Parallel/Sequential**: Parallel with T-31 (test-writing only; GREEN depends on T-12, T-29,
  T-32, T-14/T-16, and T-37's `.env.example` addition). Sequential RED before T-34 GREEN.

### [x] T-34: GREEN — implement `ClassifyArticleUseCaseWiring`
- File: `src/infrastructure/wirings/classify_article_use_case_wiring.py` — exact code from
  design.md: `create_use_case()`, `_get_article_classifier()` (assembles `ArticleClassifier` with
  `ImrydSignalDetector()`, `ArticleClassificationTextSampler()`,
  `ArticleClassificationResponseParser()`,
  `read_text_resource(PROMPTS_DIR, "s4_s5_s6_signal_prompt.txt")`,
  `temperature=float(getenv("ARTICLE_CLASSIFIER_TEMPERATURE", "0.1"))`,
  `num_predict=int(getenv("ARTICLE_CLASSIFIER_NUM_PREDICT", "300"))`), `_get_llm_generator()`
  (duplicated verbatim from `AnalyzeQualityUseCaseWiring` — 2 occurrences of a 3-line method is
  below this project's duplication tolerance per design's explicit note).
- **Satisfies**: same requirement as T-33, plus the "Wiring produces a usable use case instance"
  scenario.
- **Parallel/Sequential**: Sequential after T-12 (options param), T-14/T-16 (`read_text_resource`
  + prompt file), T-29 (full `ArticleClassifier`), T-32 (`ClassifyArticleUseCase`), T-33 (RED).

---

## Phase 12 — Config files (no test; static content)

### [x] T-35: Add `ARTICLE_CLASSIFIER_TEMPERATURE`/`ARTICLE_CLASSIFIER_NUM_PREDICT` to `.env.example`
- File: `.env.example` — append `ARTICLE_CLASSIFIER_TEMPERATURE=0.1` and
  `ARTICLE_CLASSIFIER_NUM_PREDICT=300`, matching legacy's exact hardcoded tuning values. Read the
  current file first to confirm exact formatting/grouping convention used by Slice 5's existing
  entries (`OLLAMA_MODEL_NAME`, `OLLAMA_BASE_URL`, `QUALITY_MIN_SAMPLE_WORD_COUNT`,
  `QUALITY_TEXT_SAMPLE_CHARACTER_LIMIT`) before appending, so the new lines match house style.
- No test file — static text, same convention as Slice 5's prompt `.txt` files and its own
  `.env.example` addition (PR-B T-29).
- **Satisfies**: "ClassifyArticleUseCaseWiring Owns Tunable Defaults" — documents the `.env`
  override surface for the 2 new tunables.
- **Parallel/Sequential**: Parallel with Phase 0-11 (fully independent file). No third-party
  dependency addition needed — `ollama`/`python-dotenv` already present from Slice 5.

---

## Phase 13 — Smoke parity test

### [x] T-36: Write `tests/smoke/test_classify_article_parity.py`
- File: `tests/smoke/test_classify_article_parity.py` — exact code from design.md (ADR-9):
  `TestCase` + `setUpClass()` shape mirroring `test_validate_structure_parity.py`, against the
  same 3 real `.docx` files (`1. test_Científico.docx`, `2. test_divulgacion_v2.docx`,
  `3. test_opinion_v2.docx`). Patch BOTH sides' LLM call with a canned response
  (`{"response": "S4: SI\nS5: SI\nS6: SI"}`) so the test never touches a live Ollama instance:
  - Legacy patch target: `business_logic.article_classifier.ollama.Client.generate` (instance
    method on `ollama.Client` — confirmed against actual legacy source, NOT module-level).
  - New-side patch target:
    `src.infrastructure.adapters.llm_generator.ollama_generator_adapter.ollama.generate`
    (module-level function — confirmed against `OllamaGeneratorAdapter.generate()`'s actual call).
  - These are NOT interchangeable — verify both patches actually intercept (e.g. via the mock's
    `call_count`) rather than silently falling through to a real Ollama call.
- 3 test methods (`test_cientifico_parity`, `test_divulgacion_parity`, `test_opinion_parity`),
  each asserting `new.article_type.value == legacy.article_type.value` and
  `new.confidence == legacy.confidence` (NOT asserting `reasoning` — already covered exhaustively
  by Phase 8's per-case domain unit tests; re-asserting against canned-LLM real documents would
  duplicate coverage without adding confidence).
- Real `.docx` parsing IS exercised on both sides (only the LLM network call is faked) —
  deterministic signals (IMRyD override, S2a/S2b/S3) still run against real parsed text.
- **Satisfies**: cross-cutting end-to-end parity confirmation — supports Requirement "19-Case Rule
  Table Produces Identical Output to Legacy" at the integration level (domain-level parity already
  covered by Phase 8; this is the only task touching real sample documents).
- **Parallel/Sequential**: Sequential after T-15 (regression gate cleared), T-29 (full
  `ArticleClassifier`), T-34 (wiring). Can run in parallel with T-35, T-37+.

---

## Phase 14 — Cross-cutting verification (sequential, after all GREEN)

### [x] T-37: Verify no class named `StructureAnalyzer` exists under `src/domain/`
- Grep the full `src/domain/` tree for `class StructureAnalyzer`; assert zero matches.
- Confirm `src/domain/structure/structure_validator.py`'s `StructureValidator` class definition,
  `_SECTION_ALIASES` table, and `validate()` method are byte-for-byte unchanged from before this
  slice (e.g. via `git diff` showing no modifications to that file).
- **Satisfies**: Requirement "Naming Collision Avoidance with StructureValidator" (both
  scenarios).
- **Parallel/Sequential**: Parallel with T-38, T-39, T-40.

### [x] T-38: Verify `ArticleType` definition is byte-for-byte unchanged
- Confirm via `git diff src/domain/enums/article_type.py` (or equivalent) that this slice made
  zero modifications to the file — member names (`CIENTIFICO`, `DIVULGACION`, `OPINION`, and
  `UNKNOWN` if present) and values are identical to their pre-slice state.
- **Satisfies**: Requirement "ArticleType Member Names Stay Unchanged" (the one scenario).
- **Parallel/Sequential**: Parallel with T-37, T-39, T-40.

### [x] T-39: Verify no raw confidence literals remain in the rule table
- Grep `src/domain/classification/article_classifier.py` for the bare float literals `0.95`,
  `0.90`, `0.86`, `0.85`, `0.83`; assert none appear outside
  `src/domain/enums/classification_confidence.py` itself (i.e. the rule table and IMRyD override
  path reference only `ClassificationConfidence` members, never raw floats).
- **Satisfies**: Requirement "ClassificationConfidence Enum Replaces Inline Confidence Literals"
  ("no raw literals remain" scenario).
- **Parallel/Sequential**: Parallel with T-37, T-38, T-40.

### [x] T-40: Verify zero `print()` calls in all new files
- Grep every file introduced or modified by this slice (signal detector, text sampler, response
  parser, domain service, both enums, use case, wiring, the retrofitted
  `analyze_quality_use_case_wiring.py`, `text_resource_loader.py`) for `print(`; assert zero
  matches. Confirm the legacy classifier's exception-path `print()` (in the S4/S5/S6 LLM call's
  error handler) was dropped, not replaced with logging — consistent with the `analyze-quality`
  precedent.
- **Satisfies**: Requirement "No print() Statements in New Code" (the one scenario).
- **Parallel/Sequential**: Parallel with T-37, T-38, T-39.

### [x] T-41: Verify zero file I/O / infrastructure imports in `src/domain/classification/`
- Grep `imryd_signal_detector.py`, `article_classification_text_sampler.py`,
  `article_classification_response_parser.py`, `article_classifier.py` for `open(`, `import os`,
  `from os`, `dotenv`, `from src.infrastructure`, `import ollama`; assert zero matches across all
  4 files.
- **Satisfies**: Requirement "ArticleClassifier Domain Service Orchestrates Classification" —
  "Domain service has zero infrastructure imports" scenario (final confirmation, beyond T-20's
  per-file check, across the whole `classification/` package).
- **Parallel/Sequential**: Sequential after T-37, T-38, T-39, T-40.

### [x] T-42: ruff check on all new/modified files
- Run `ruff check` against every new/modified file in this slice: both enums
  (`classification_confidence.py`, `article_size.py`), the 4 classification domain files,
  `text_resource_loader.py`, the retrofitted `analyze_quality_use_case_wiring.py`,
  `classify_article_use_case.py`, `classify_article_use_case_wiring.py`,
  `ollama_generator_adapter.py`, `llm_generator_port.py`, the prompt `__init__.py`, and all new/
  modified test files (domain, application, infrastructure, smoke).
- Fix any lint findings before proceeding to T-43.
- **Satisfies**: general code-quality gate, not requirement-specific.
- **Parallel/Sequential**: Sequential after T-41.

### [x] T-43: Full regression suite run (final gate)
- Run `python -m pytest src/ -q` — confirm the pre-slice baseline (284 passed from Slice 5 PR-B)
  plus this slice's full new test count, zero regressions.
- Run `python -m pytest tests/smoke/ -q` separately — confirm the new
  `test_classify_article_parity.py` passes (3 tests) alongside the existing
  `test_validate_structure_parity.py` and any other smoke tests, with no live Ollama dependency
  triggered (both patch targets from T-36 intercepted correctly).
- **Satisfies**: overall slice acceptance gate — confirms the full migration preserved legacy
  behavior while restructuring, including the Phase 6 retrofit of already-merged Slice 5 code.
- **Parallel/Sequential**: Sequential, last task.

---

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated new/modified files | ~28 (12 new production files, 1 modified production file outside this slice's own new surface [`analyze_quality_use_case_wiring.py` retrofit], 2 modified files [`llm_generator_port.py`, `ollama_generator_adapter.py`], ~13 new test files, 1 modified test file [`test_ollama_generator_adapter.py`], 1 new smoke test file, `.env.example` append) |
| Estimated changed lines | ~950-1100 |
| 400-line budget risk | **High** |
| Chained PRs recommended | **Assessment: comparably sized to analyze-quality's combined PR-A+PR-B total (~480-540 + ~180-220 ≈ 660-760), but larger** — driven primarily by Phase 8's 4-way classifier split (signal detector + sampler + parser + orchestrator with an 18-row rule table) carrying more transcription volume than analyze-quality's 2-way split, plus this slice's unique Phase 6 retrofit task touching already-merged code. |
| Decision needed before apply | **Yes** |

### Breakdown

- New production files: `imryd_signal_detector.py` (~25), `classification_confidence.py` (~12),
  `article_classification_text_sampler.py` (~35), `article_classification_response_parser.py`
  (~15), `article_classifier.py` (~280 — the largest single file: dataclass + constants + 7
  signal/orchestration methods + 18-row `_RULE_TABLE` + 19 `_reasoning_case_N` functions),
  `text_resource_loader.py` (~8), `classify_article_use_case.py` (~10),
  `classify_article_use_case_wiring.py` (~30), `prompts/classification/__init__.py` (~3),
  `s4_s5_s6_signal_prompt.txt` (~15), `classify_article_size()` addition to `article_size.py`
  (~12 added lines). Subtotal: **~445**.
- Modified production files: `llm_generator_port.py` (~2-line signature change),
  `ollama_generator_adapter.py` (~3-line signature + forwarding change),
  `analyze_quality_use_case_wiring.py` (retrofit: ~10 lines removed, ~4 lines added — net
  negative diff, but full method deletion + 2 call-site rewrites touch a meaningful fraction of
  the file). Subtotal: **~20 net, ~30 gross diff**.
- New test files: `test_imryd_signal_detector.py` (~50), `test_classification_confidence.py`
  (~15), `test_classify_article_size.py` (~20), `test_article_classification_text_sampler.py`
  (~40), `test_article_classification_response_parser.py` (~20),
  `fake_llm_generator_port.py` (~20, test double not a `TestCase`),
  `test_article_classifier_signals.py` (~70), `test_article_classifier_imryd_override.py` (~50,
  includes T-30's empty-paragraphs test), `test_article_classifier_cientifico.py` (~60),
  `test_article_classifier_divulgacion_near_miss.py` (~50),
  `test_article_classifier_divulgacion_standard.py` (~90),
  `test_article_classifier_opinion.py` (~30), `test_classify_article_use_case.py` (~20),
  `test_classify_article_use_case_wiring.py` (~25), `test_text_resource_loader.py` (~15).
  Subtotal: **~575**.
- Modified test file: `test_ollama_generator_adapter.py` (+2 new test methods, ~25 lines added).
- New smoke test file: `test_classify_article_parity.py` (~55).
- `.env.example`: +2 lines.
- **Total estimated diff**: **~950-1100 lines changed/added** — roughly 1.4-1.6x
  `analyze-quality`'s combined PR-A+PR-B total (~660-760 lines), even though this is a single
  slice rather than 2. The dominant driver is `article_classifier.py` itself (~280 lines for one
  file, vs. `quality_analyzer.py`'s ~75-line rewrite) plus its 6 corresponding test files
  (~370 combined) — the 18-row rule table with per-row reasoning functions is structurally larger
  than `analyze-quality`'s equivalent orchestration logic.

### Decision needed before apply: Yes

Per `delivery_strategy: ask-on-risk`, the orchestrator MUST stop and ask the user whether to split
this slice into chained/stacked PRs before running `sdd-apply`, or proceed with a `size:exception`
label for a single PR. Suggested split points if chaining is chosen (mirroring this tasks file's
own phase boundaries, each a coherent, independently-mergeable unit):

| Candidate PR | Phases | Rationale |
|---|---|---|
| PR-1 | Phase 0-7 (signal detector, confidence enum, `classify_article_size`, sampler, parser, port/adapter `options`, shared `read_text_resource()` + retrofit, prompt file) | All supporting collaborators + the Phase 6 retrofit gate (T-15) isolated from the highest-risk Phase 8 transcription — lets the retrofit's regression risk be reviewed and merged independently of the large rule-table diff. |
| PR-2 | Phase 8-9 (`_ClassificationSignals`, `_RULE_TABLE`, `ArticleClassifier` orchestrator, empty-paragraphs validation) | The highest-risk, highest-volume unit (~280 production lines + ~370 test lines) isolated into its own review — reviewer's job here is specifically "confirm 18-row transcription parity," a narrower and more scrutiny-appropriate review scope than mixing it with wiring/use-case plumbing. |
| PR-3 | Phase 10-14 (use case, wiring, config, smoke parity test, cross-cutting verification) | Thin integration layer + final gates, low individual risk, natural closing PR. |

This split mirrors `analyze-quality`'s own PR-A (domain)/PR-B (adapter+use case+wiring) precedent,
but adds a 3-way cut specifically because Phase 8 alone is comparable in size to all of
`analyze-quality`'s PR-A. Do not decide chaining unilaterally — surface this explicitly to the
user per the `ask-on-risk` strategy and let them choose between this 3-way split, a 2-way split
(PR-1+6 combined as "supporting code," PR-8 standalone, PR-rest), or a single PR with
`size:exception`.
