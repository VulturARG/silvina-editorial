# Feature: Full-Text Analysis Refactor Study

- **Feature Name**: `full-text-analysis-refactor-study`
- **File Locator**: `odd/tasks/full-text-analysis-refactor-study.md`
- **Type**: Analysis only. No source changes until the user approves a design.
- **Commit policy**: stop before every commit and wait for the user's instructions

---

## 1. Objective

Study how to refactor the analyzers so that each LLM and grammar stage reads the **whole document body** by default, without having to tune several overlapping limits. Today a full-text analysis requires touching many parameters, which is unnecessary complexity.

## 2. Evidence (sandbox/pack_2, `01_IMRyD_Cano_Martinez.docx`, 49 392 chars, 7 219 words)

- Quality stages (clarity/coherence, argumentation/conclusions, editorial suitability) received 32 490 chars (65.8 %). The text ended at the first paragraph of "Discusión"; the "Conclusión" section (starts at char 34 895) never reached the model, so both Haiku and Gemma reported "no formal conclusions".
- Cause: `QualityTextSampler.build_sample` falls back to the whole document whenever the strategic sample has fewer than `[quality].min_sample_word_count = 10000` words, then cuts at `[quality_text_sample].character_limit = 32000`. The strategic path (intro + middle + conclusion) is therefore never used.
- The fallback path does not strip the bibliography; the strategic path does (`_is_reference_like`). `ArticleClassificationTextSampler._strip_bibliography` implements a separate, similar rule.
- Grammar is capped twice: `[grammar].max_paragraphs = 20` and `max_chars = 5000` (raising `max_chars` alone changes nothing). The check returned 0 errors on a text that has at least one clear error ("terminan favorecieron").
- Raising `OLLAMA_NUM_CTX` to 24576 is required for ~60 000 chars (about 16 000 tokens); the sampling limits are independent knobs that must stay consistent with it.
- `QualityResponseParser` fills a missing dimension with the "No disponible / 7.0" placeholder, and `QualityAnalyzer._ensure_call_produced_usable_content` only requires one of the two dimensions of a call. Haiku answered `## 2. Coherencia [Puntuación: 6/10]` (no `**`), the header pattern did not match, and the real score was replaced by 7.0 (3 of 18 Haiku 4.5 quality calls so far).

## 3. Questions the study must answer

1. Which limits exist today for the same concern (sampling, truncation, context)? List them with owner, default and where each is read.
2. Can a single source of truth derive the per-stage text from the context window (`OLLAMA_NUM_CTX` / provider limit) instead of fixed character counts?
3. What should happen when the body exceeds the context: fail fast, truncate the middle, or summarize sections? Conclusions must never be silently dropped.
4. Where should "body without bibliography" live so classification, quality and grammar share one implementation (domain service or `DocumentContentDTO` field)?
5. Should sampling remain an opt-in mode (e.g. for very small local models) rather than the default?
6. How should the parser and analyzer fail when a requested dimension is missing, and should header matching tolerate `#` headings?
7. Impact on latency and cost per provider (measure on `data/metrics.db`: Haiku ~68 s, Gemma ~178 s per analysis today).

## 4. Tasks

- [ ] **TASK-01: Inventory of text limits and sampling paths** (read-only; settings, wiring, samplers, grammar adapter, docs)
- [ ] **TASK-02: Measure token and latency cost of full-text input** (Gemma local and Haiku/Sonnet, using `data/metrics.db` plus one controlled run)
- [ ] **TASK-03: Design options with trade-offs and a recommendation** (single full-body default, context-derived limit, overflow policy, shared bibliography stripping)
- [ ] **TASK-04: Parser robustness proposal** (dimension header tolerance, fail on missing dimension)
- [ ] **TASK-05: Present the design to the user and wait for approval before any implementation**
