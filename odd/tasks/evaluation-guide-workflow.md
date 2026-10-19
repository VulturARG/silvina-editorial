# Feature: Evaluation workflow of the Guía de Evaluación v1.1

- **Feature Name**: `evaluation-guide-workflow`
- **File Locator**: `odd/tasks/evaluation-guide-workflow.md`
- **Branch**: `silvina_editorial_v300` (created from `silvina_editorial_v200`)
- **Status**: PLAN ONLY. Nothing here is started or authorized for execution. The plan is expected to change; the source document is still a working draft.
- **TDD Mode**: Test-first (RED then GREEN) for every task with runnable deterministic tests
- **TDD Runner**: `export APP_MODE=PROD; .venv/Scripts/python.exe -m unittest discover -s src -t . -p "test_*.py"` and the same with `-s tests`
- **Commit policy**: one work-unit commit per task (Conventional Commits); push, PR and merge stay the user's decisions

---

## 1. Objective

Bring the analysis pipeline (`AnalyzeDocumentUseCase`) in line with the workflow of section 3 of `E:\Python\silvina-doc\2026-10-18_Silvina_Guia_Evaluacion_v1.1.docx` (stages 0 to 7). Scope is the flow of stages; the technical conditions of section 3.1 are configuration, not part of this plan. The comparison between the proposal and the current system is in `docs/comparacion_flujo_guia_evaluacion_v1.1.md`.

## 2. Evidence

- `AnalyzeDocumentUseCase._run_pipeline` (`src/application/analyze_document_use_case.py`) runs: extract content, length check, citations, APA, grammar, classification, quality, structure, citation matching, EUMIC, recommendations and verdict. The stage names are the `AnalysisStage` enum.
- The use case only orchestrates. IMRyD override, the LLM signal call and the rule table live in `ArticleClassifier`; the contribution and alignment calls live inside `QualityAnalyzer.analyze` through `EditorialSuitabilityAnalyzer`.
- Blast radius measured by files mentioning the affected symbols (production / tests; one file may count in several rows): length check 7/7; reference signals 7/12; classifier, IMRyD and vocabulary 8/10; signal parser, signals DTO and prompt 13/13; rule table, specifications and confidence 12/15; alignment 13/34; contribution 12/22; quality DTOs and report consumers 26/38; verdict and recommendations 18/12; use case, wiring and stages 7/14.
- `ReportInputDTO.quality` is mandatory. It is read by `PublicationVerdictEvaluator`, `QualityRule`, `DimensionRule`, the DOCX executive summary, quality and suitability sections, `JsonReportAdapter` and `ReportInputDTO.is_publishable`.
- `LlmGeneratorPort.generate(prompt, options)` has no structured-output parameter, and no adapter in `src/infrastructure/adapters/llm_generator/` passes a `format` argument. Current parsers read labeled plain text.
- Prompts are read from `src/infrastructure/resources/prompts/{classification,quality}/` (default set) with a second set in `v2/`, selectable by CLI.
- The length limit is `max_body_chars` in `editorial_norms.toml` (`[article_length]`, now 75000), measured on title plus body without bibliography; there is no minimum. `DocumentBodyTooLong` is raised by `ArticleLengthChecker`.
- `scripts/regenerate_json_export_golden_fixture.py` and `tests/e2e` exist, so the JSON export shape is pinned by tests.
- Sourced findings on asking a model for JSON (researched 2026-10-19):
  - Ollama enforces a JSON schema passed in the `format` field (grammar-constrained decoding); its documentation recommends also placing the schema in the prompt and using temperature 0 (https://docs.ollama.com/capabilities/structured-outputs).
  - "Let Me Speak Freely?" (EMNLP Industry 2024, https://arxiv.org/abs/2408.02442): forced JSON lowers reasoning accuracy and helps or matches classification accuracy; key order matters, because a model that wrote `answer` before `reason` lost its chain of thought. Models tested: GPT-3.5, Claude 3 Haiku, Gemini 1.5 Flash, LLaMA-3-8B, Gemma-2-9B (not Gemma 4).
  - Preprint on 0.6B to 4B models (https://arxiv.org/html/2609.23742): constrained decoding brings schema validity to 100% but does not fix semantic errors.
  - Single-author blog test, 20 emails and 6 small models (https://aitoollabs.dev/posts/small-llm-json-output/), indicative only: grammar 87/120 correct vs 88/120 without it; grammar with no schema in the prompt 47/120; unconstrained replies were often wrapped in Markdown fences.
  - Ollama bug #15260: with `think=false`, `format` was silently ignored for `gemma4`; fixed by PR #15678 (merged 2026-04-21) and limited to the `gemma4` parser. Related: #15386 (decision made in reasoning not reflected in the JSON, `gemma4:31b`).
  - Not verified: this project runs `gemma4-26b-adapted` (Modelfile `PARSER gemma4`) with `OLLAMA_THINK=false`; the local Ollama client is 0.35.1 and no model is installed on this machine, so whether the fix applies is unknown.

## 3. Design (direction only, to be confirmed)

- Strangler approach for the classification: build the new signals and rules next to the old ones, switch the classifier, then remove the old code. Every task leaves both suites green.
- The use case keeps orchestrating; stage logic stays in domain services behind the existing ports. Concrete adapters are created only in `src/infrastructure/wirings/`.
- Anything marked "blocked by decision" in section 4 must not start before the matching item of section 5 is answered.

## 4. Tasks

### Phase 0: preliminary check

- [ ] **TASK-00: Smoke test of `format` with the real model**
  - **Scope**: a throwaway script outside `src/` (not committed unless the user decides so) that calls the real model (`gemma4-26b-adapted`) through the Ollama client with `think=false` and a JSON schema in `format`, in two variants: schema only in `format`, and schema also written in the prompt. Record Ollama version, model and results in this document.
  - **Acceptance**: for each variant, the share of responses that are valid JSON and validate against the schema over a fixed set of the sample documents in `docs/sample-documents/`; the finding decides D4.
  - **Needs**: Ollama running and the model installed (neither is true on the development machine today).

### Phase A: independent of the pending items of the document

- [ ] **TASK-01: Admission minimum**
  - **Scope**: `ArticleLengthNormsDTO`, `editorial_norms_loader.py`, `editorial_norms.toml`, `ArticleLengthChecker`, a new domain error for a body that is too short, and the places that report `DocumentBodyTooLong`, with tests.
  - **Acceptance**: both limits come from configuration; a body below the minimum is rejected before any other stage.
  - **Depends on**: decisions D1 and D2.
- [ ] **TASK-02: Group the formal checks (stage 1)**
  - **Scope**: `analyze_document_use_case.py` and its tests: citation matching and EUMIC inspection run with APA and grammar, before the classification.
  - **Acceptance**: pipeline order matches stages 0 and 1; stage names and recorded metrics unchanged.
- [ ] **TASK-03: Remove the contribution evaluation**
  - **Scope**: contribution call, parser, observation builder, verdict enum, DTO fields, DOCX and JSON report fields, `contribution_prompt.txt` in both prompt sets, and their tests.
  - **Acceptance**: no contribution call or report field remains; the alignment evaluation keeps working until TASK-09.

### Phase B: classification (stages 2, 3 and 4)

- [ ] **TASK-04: New signals and rules R1 to R3 (domain only)**
  - **Scope**: new signals DTO (C1 to C5, D1 to D4) and a rule evaluator for R1, R2 and R3 with high or medium confidence, next to the old table, with pure domain tests.
  - **Acceptance**: the three rules and the confidence levels of section 2.2 of the document are covered by tests; nothing is wired yet.
- [ ] **TASK-05: Deterministic signal C2**
  - **Scope**: `ArticleClassifier` or a new detector: IMRyD complete or methodological vocabulary gives C2; IMRyD no longer decides the type nor skips the LLM.
  - **Acceptance**: tests show IMRyD alone does not classify as scientific.
- [ ] **TASK-06: Two chained LLM calls (1A then 1B)**
  - **Scope**: a service for each call, response parsers, the hand-over of the purpose quote from 1A to 1B, new prompt files, wiring.
  - **Acceptance**: C1, C3, C4, C5, D1 to D4 are produced from the two responses; the call order and the data passed are covered by tests with a fake generator.
  - **Depends on**: TASK-00 and decisions D3, D4 and D5.
- [ ] **TASK-07: Switch the classifier and remove the old code**
  - **Scope**: `ArticleClassifier` uses TASK-04 to TASK-06; remove the old rule table, specifications, S4 to S6 prompt and parser; update `ClassificationResultDTO` consumers and reports.
  - **Acceptance**: both suites and ruff are green with no reference to the removed classes.
  - **Depends on**: decision D6.
- [ ] **TASK-08: Bibliographic backing out of the classification**
  - **Scope**: reference count and recency leave the classification signals and become a formal observation that moves on to the next stage.
  - **Acceptance**: classification no longer depends on references; the datum is still produced.
  - **Blocked by decision**: D7.

### Phase C: pertinence and quality (stages 5 and 6)

- [ ] **TASK-09: Pertinence from the first LLM call**
  - **Scope**: take the alignment evaluation out of `QualityAnalyzer`; pertinence is produced by call 1A.
  - **Blocked by decision**: D8.
- [ ] **TASK-10: Pertinence gate and report without quality**
  - **Scope**: the use case skips the quality calls when the document is not aligned and the editor has not forced them; `ReportInputDTO.quality` becomes optional; verdict, recommendations, DOCX, JSON and web consumers handle its absence.
  - **Acceptance**: a not-aligned document runs 2 calls, an aligned one runs 4.
  - **Blocked by decision**: D8 and D9.
- [ ] **TASK-11: Quality scale and prompts 2 and 3**
  - **Scope**: levels 1 to 5, the prompts of the document, and the conversion to score.
  - **Blocked by decision**: D10.

### Phase D: verdict and closure

- [ ] **TASK-12: Verdict and report (stage 7)**
  - **Scope**: `PublicationVerdictEvaluator`, recommendation rules and report sections for the new inputs.
  - **Blocked by decision**: D10 and D11.
- [ ] **TASK-13: Verification and docs**
  - **Scope**: full `src` and `tests` suites, ruff, JSON golden fixture regeneration if the export changed, README and `docs/` update. Verification is delegated to `gentle-ai-verify`.

## 5. Open decisions (pending user confirmation)

- **D1**: what counts toward the 5.000 and 35.000 characters (title, tables, bibliography). The values come from configuration.
- **D2**: default values of both limits in `editorial_norms.toml`, and whether the current 75.000 is replaced.
- **D3**: are the prompts of section 4 of the document part of the implementation, and which prompt set (default or `v2`) do they replace?
- **D4**: structured JSON output needs a `format` argument that `LlmGeneratorPort` and the Ollama and Claude adapters do not have. Is that in scope, or do the new calls keep the labeled-text format? Evidence in section 2; TASK-00 checks it against the real model before deciding.
- **D5**: JSON schemas of the prompts are still a pending item of the document.
- **D6**: the current system validates structure by category and classifies article size; the document does not mention them. Keep, change or remove?
- **D7**: where does the bibliographic backing datum appear after stage 1 (report, verdict, recommendation)?
- **D8**: pertinence is "pendiente" in the document: definition, research lines, and whether it comes from call 1A.
- **D9**: how does the editor force the quality evaluation (CLI flag, web control, other), and what does the report without quality contain?
- **D10**: conversion of levels 1 to 5 to a score and the verdict thresholds are pending in the document.
- **D11**: should the verdict keep today's three states (APTO, REQUIERE REVISIÓN, NO APTO)?
- **D12**: is the JSON export contract consumed outside this repository?

## 6. Out of scope

- Section 3.1 technical conditions (context window, shared header, full-read check, seed, scalability): configuration.
- Validation with the test documents (item 4 of the pending list of the document).
