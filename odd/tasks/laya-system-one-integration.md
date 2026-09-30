# Feature: Laya System One Integration

- **Feature Name**: `laya-system-one-integration`
- **File Locator**: `odd/tasks/laya-system-one-integration.md`
- **TDD Mode**: Enabled (Strict TDD: RED -> GREEN -> REFACTOR)
- **TDD Runner**: `.venv\Scripts\python -m pytest src/`
- **Delivery Strategy**: `ask-on-risk`
- **Forecast Changed Lines**: ~250 lines
- **Running Authored Lines**: 0

---

## 1. Objective & Problem
Integrate LAYA as a non-autoregressive System 1 decision engine in Silvina Editorial to evaluate and classify academic documents in milliseconds (~30ms GPU, ~150-200ms CPU), decoupling deterministic decision/scoring logic from generative qualitative feedback (LLM / Ollama).

As a prerequisite to loading the trained Laya checkpoint, the domain must decouple its current direct dependency on `LlmGeneratorPort` and prompt templates. In accordance with Clean Hexagonal Architecture (`.agent/skills/clean-architecture/SKILL.md`), we extract clean domain ports and implement an initial backward-compatible adapter before plugging in the concrete `LayaDecisionAdapter`.

## 2. Scope & Constraints

### In Scope (Phase 1: Domain Ports & Contract Extraction)
- Extract domain port `ResearchIntentDetectorPort` under `src/domain/classification/`.
- Implement `OllamaResearchIntentAdapter` under `src/infrastructure/adapters/classification/` fulfilling the port to preserve current behavior.
- Refactor `ArticleClassifier` domain service to depend strictly on `ResearchIntentDetectorPort`.
- Update `AnalyzeDocumentUseCaseWiring` to construct and inject the port/adapter chain.
- Strict TDD unit tests for both the domain service (pure Python, fake double) and the infrastructure adapter.
- Full regression test suite passing.

### Out of Scope
- Training pipeline execution (performed externally in dedicated environment).
- Modifying `QualityAnalyzer` and `EditorialSuitabilityAnalyzer` (will be addressed in Phase 2).
- Breaking public use case interfaces.

---

## 3. Checklist of Actionable Tasks

- [x] **TASK-01: Define domain port `ResearchIntentDetectorPort`**
  - **Route**: direct inline
  - **Scope**: Create `src/domain/classification/research_intent_detector_port.py` with abstract method `detect(text_sample: str, title: str | None) -> tuple[bool, bool, bool]`. Follow PEP 604 union types, no abbreviations, proper docstrings.
  - **Verification**: Unit tests in `src/domain/tests/classification/test_research_intent_detector_port.py`.

- [x] **TASK-02: Implement `OllamaResearchIntentAdapter`**
  - **Route**: direct inline
  - **Scope**: Create `src/infrastructure/adapters/classification/ollama_research_intent_adapter.py` implementing `ResearchIntentDetectorPort` by delegating to `LlmGeneratorPort`, prompt template rendering, and `ArticleClassificationResponseParser`.
  - **Verification**: Unit tests in `src/infrastructure/tests/adapters/classification/test_ollama_research_intent_adapter.py`.

- [x] **TASK-03: Refactor `ArticleClassifier` to depend on `ResearchIntentDetectorPort`**
  - **Route**: direct inline
  - **Scope**: Update `src/domain/classification/article_classifier.py` constructor to receive `research_intent_detector: ResearchIntentDetectorPort` instead of `llm_generator`, `signal_prompt_template`, `temperature`, `num_predict`, and `response_parser`.
  - **Verification**: Update `src/domain/tests/classification/test_article_classifier.py` with a fake test double implementing `ResearchIntentDetectorPort`.

- [x] **TASK-04: Update `AnalyzeDocumentUseCaseWiring`**
  - **Route**: direct inline
  - **Scope**: Update `src/infrastructure/wirings/analyze_document_use_case_wiring.py` method `_get_article_classifier()` to instantiate `OllamaResearchIntentAdapter` and inject it.
  - **Verification**: Test wiring and integration in `src/infrastructure/tests/wirings/test_analyze_document_use_case_wiring.py` or existing wiring tests.

- [x] **TASK-05: Regression Verification & Work-Unit Commit**
  - **Route**: direct inline
  - **Scope**: Run full pytest suite across `src/` (685+ tests). Ensure zero regressions.
  - **Verification**: Commit work-unit to `feat/laya-system-one-ports`.

### Phase 2: Synthetic Dataset Generation & Laya Fine-Tuning
- [x] **TASK-06: Define the 56-Archetype Combinatorial Matrix Specification**
  - **Route**: direct inline
  - **Scope**: Create `E:/IA/laya/data/silvina_editorial/archetypes_specification.json` defining the 56 combinations (7 defense lines x 8 boolean profiles) with realistic subthemes, signal criteria, and ground truth.
  - **Verification**: Integrity test in Python asserting 56 distinct archetypes.

- [x] **TASK-07: Implement Batch Synthetic Dataset Generator**
  - **Route**: direct inline
  - **Scope**: Implement modular generator in `E:/IA/laya/scripts/generate_full_dataset.py` capable of batch-generating 1.000–1.200 word academic texts conforming to canonical Laya schema (`max_len=2048`).
  - **Verification**: Execute generator on first batch and verify word counts and question schemas.

- [x] **TASK-08: Generate Full Dataset (~450-500 samples)**
  - **Route**: subagent delegation / batch execution
  - **Scope**: Generate complete dataset covering all 56 archetypes plus out-of-domain controls.
  - **Verification**: Line count, word count distribution, and JSONL format validation.

- [x] **TASK-09: Stratified Partitioning (Train / Calibration / Test)**
  - **Route**: direct inline
  - **Scope**: Split raw dataset into `train.jsonl` (80%), `calibration.jsonl` (10%), and `test.jsonl` (10%) with balanced representation across archetypes.
  - **Verification**: Assert non-overlapping splits, seed reproducibility, and calibration holdout integrity.

- [x] **TASK-10: Generate Teacher Gold Distributions via Ollama**
  - **Route**: direct inline / batch execution
  - **Scope**: Generate the `gold` field (per-question teacher probability distributions) required by Laya's RLCD fine-tuning format, by sampling each `state`+`questions` against Ollama K=5 times at temperature 0.7 and computing empirical frequency per question.
  - **Verification**: All 480 records (384 train + 48 calibration + 48 test) carry `gold` with all 9 question ids and probabilities summing to 1.0.

### Phase 3: Wire `LayaDecisionAdapter` into Production

- [x] **TASK-12: Define domain port `LayaDecisionPort` and `LayaDecisionResultDTO`**
  - **Route**: direct inline
  - **Scope**: Create `src/domain/laya/laya_decision_port.py` (abstract method `decide(text_sample: str) -> LayaDecisionResultDTO`) and `src/domain/dtos/laya_decision_result_dto.py` carrying the 9 raw decisions from `decision_questions.json` (`s4_research_intent`, `s5_empirical_evidence`, `s6_theoretical_framework` — renamed from the `s4_intent`/`s5_evidence`/`s6_theory` question ids to avoid opaque abbreviations, so `LayaDecisionAdapter` maps ids to fields —, `editorial_verdict`, `research_line` as `LayaChoiceDecisionDTO` carrying `answer`, per-option `probabilities` and `confidence`; `score_clarity`, `score_coherence`, `score_argumentation`, `score_conclusions` as `LayaScoreDecisionDTO` carrying the 0-10 `expected_value` and `confidence`). Confidence is Laya's `answer_confidence` (calibrated probability of the reported answer), kept so downstream services can request LLM narrative when Laya is uncertain.
  - **Verification**: Unit tests in `src/domain/tests/laya/test_laya_decision_port.py` and `src/domain/tests/dtos/test_laya_decision_result_dto.py`.

- [x] **TASK-13: Implement the Laya text sampler**
  - **Route**: direct inline
  - **Scope**: Create `src/domain/laya/laya_text_sampler.py` building the single Laya `state` with the same strategy the pre-Laya `QualityTextSampler` used (the legacy sampler that loaded the most characters): title + first 3 paragraphs + 2 middle paragraphs + up to 3 conclusion paragraphs (or the last 2 non-reference paragraphs), joined up to 8000 characters completing the boundary paragraph, falling back to the full document when the excerpt has fewer than 400 words. Every parameter is injected (no hardcoded defaults) and read from `.env` via `EnvConfig` (`LAYA_TEXT_SAMPLE_*`).
  - **Verification**: Unit tests in `src/domain/tests/laya/test_laya_text_sampler.py` covering each parameter and the fallback, plus `EnvConfig` default/override tests.

- [x] **TASK-14: Implement `LayaDecisionAdapter`**
  - **Route**: direct inline
  - **Scope**: Create `src/infrastructure/adapters/laya/laya_decision_adapter.py` implementing `LayaDecisionPort` via an injected, already-loaded Laya `Agent` and its question definitions (the wiring calls `laya.load(checkpoint_path)` and reads `src/infrastructure/resources/laya/decision_questions.json`), calling `agent.predict(state, questions)` once and mapping the raw `choice`/`score` answers into `LayaDecisionResultDTO`.
  - **Verification**: Unit tests in `src/infrastructure/tests/adapters/laya/test_laya_decision_adapter.py` with a faked/mocked Laya agent (no real checkpoint load in unit tests).

- [x] **TASK-15: Implement the `LayaDecisionMaker` domain service**
  - **Route**: direct inline
  - **Scope**: Create `src/domain/laya/laya_decision_maker.py` injecting `LayaTextSampler` and `LayaDecisionPort`, exposing `decide(document_content: DocumentContentDTO) -> LayaDecisionResultDTO` (build the `state` once, call the port once). Per the clean-architecture skill the use case must never call a port directly, so the use case orchestrates this domain service instead. The use-case integration happens incrementally in TASK-16 to TASK-18 so the suite stays green after each task.
  - **Verification**: Unit tests in `src/domain/tests/laya/test_laya_decision_maker.py` with `FakeLayaDecisionPort`.

- [x] **TASK-16: Refactor `ArticleClassifier` to consume `LayaDecisionResultDTO`**
  - **Route**: direct inline
  - **Scope**: Make `AnalyzeDocumentUseCase` call `LayaDecisionMaker.decide()` once per document and pass the resulting `LayaDecisionResultDTO` into `ArticleClassifier.classify()`. Replace the `ResearchIntentDetectorPort` dependency in `src/domain/classification/article_classifier.py` with a read of `s4_research_intent`/`s5_empirical_evidence`/`s6_theoretical_framework` from the injected `LayaDecisionResultDTO`. Retire `ResearchIntentDetectorPort` and `OllamaResearchIntentAdapter` once no longer referenced.
  - **Verification**: Update `src/domain/tests/classification/test_article_classifier.py` and `src/application/tests/test_analyze_document_use_case.py`.
  - **Outcome**: Signals map `LayaBinaryAnswer.YES` (`"SI"`) to `True`. Retired `ResearchIntentDetectorPort`, `OllamaResearchIntentAdapter`, `ArticleClassificationTextSampler`, `ArticleClassificationResponseParser`, the `s4_s5_s6_signal_prompt.txt` prompt, the classification-only `FakeLlmGeneratorAdapter`, and the `ARTICLE_CLASSIFIER_TEMPERATURE`/`ARTICLE_CLASSIFIER_NUM_PREDICT` env vars. The constructor change forced the Laya part of TASK-19 forward: the wiring now builds `LayaDecisionMaker` (`laya.load(LAYA_CHECKPOINT_PATH, device=LAYA_DEVICE)`, empty device = automatic) and `AnalyzeDocumentUseCaseWiringForTest` swaps in `FakeLayaDecisionPort`; the CLI e2e test patches `laya.load` with `FakeLayaAgent`. The living OpenSpec specs (`openspec/specs/analyze-document/spec.md`, `openspec/specs/classify-article/spec.md`) still describe the retired env vars and LLM signal path — pending update.

- [x] **TASK-17: Refactor `QualityAnalyzer` to consume Laya scores, Ollama feedback on demand**
  - **Route**: direct inline
  - **Scope**: Make `AnalyzeDocumentUseCase` pass the same `LayaDecisionResultDTO` into `QualityAnalyzer.analyze()`. Update `src/domain/quality/quality_analyzer.py` to take the 4 dimension scores directly from `LayaDecisionResultDTO`; call the LLM narrative prompts only for dimensions scoring below `QualityLevel.GOOD.min_threshold` (7.0).
  - **Verification**: Update `src/domain/tests/quality/test_quality_analyzer.py` covering both the all-above-threshold (no LLM calls) and below-threshold (LLM feedback requested) paths.
  - **Outcome**: `QualityAnalyzer.analyze(document_content, laya_decision)` takes the 4 scores from `LayaDecisionResultDTO` (overall = their mean). Each LLM prompt covers a pair (clarity+coherence, argumentation+conclusions) and is called only when a dimension of that pair scores below 7.0; the LLM score is discarded and only the feedback of the below-threshold dimensions is kept (other dimensions get an empty feedback, which the report skips). Unusable LLM output for a below-threshold dimension still raises `QualityAnalysisFailed`. `EditorialSuitabilityAnalyzer` is unchanged (TASK-18).

- [x] **TASK-18: Refactor `EditorialSuitabilityAnalyzer` to consume Laya verdicts, Ollama narrative on demand**
  - **Route**: direct inline
  - **Scope**: `QualityAnalyzer` (not the use case) calls `EditorialSuitabilityAnalyzer`, so it forwards the `LayaDecisionResultDTO` it receives. Update `src/domain/quality/editorial_suitability_analyzer.py` to take `editorial_verdict`/`research_line` from `LayaDecisionResultDTO`; call the contribution/alignment LLM prompts only when the verdict is not the positive one (`SUSTENTADA` / aligned).
  - **Verification**: Update `src/domain/tests/quality/test_editorial_suitability_analyzer.py` covering positive-verdict (no LLM calls) and negative/partial-verdict (LLM narrative requested) paths.
  - **Outcome**: Laya verdict is authoritative; LLM called for contribution only when verdict != SUSTENTADA, for alignment only when line == NINGUNA; Laya cannot express "PARCIALMENTE ALINEADO" so alignment is ALINEADO/NO ALINEADO; positive alignment has empty justification; LLM verdict discarded; docx skips empty justification.

- [ ] **TASK-19: Update `AnalyzeDocumentUseCaseWiring`**
  - **Route**: direct inline
  - **Scope**: Laya construction already landed in TASK-16; remaining: any QualityAnalyzer/EditorialSuitabilityAnalyzer wiring changes from TASK-17/18. Original scope: In `src/infrastructure/wirings/analyze_document_use_case_wiring.py`, load the agent with `laya.load` (`data/laya/checkpoints/laya_finetuned_v1_16epochs/`), read `decision_questions.json`, build `LayaDecisionAdapter`, inject it into `LayaDecisionMaker` together with `LayaTextSampler` (settings from `EnvConfig.get_laya_text_sample_settings()`), and inject `LayaDecisionMaker` into the use case.
  - **Verification**: Update `src/infrastructure/tests/wirings/test_analyze_document_use_case_wiring.py`.

- [ ] **TASK-21: Validate Laya GPU inference on AMD ROCm (before TASK-19)**
  - **Route**: direct inline
  - **Scope**: The app must run on AMD GPUs as well as NVIDIA/CPU. `requirements.txt` pins only `laya==0.3.22`; the PyTorch build is chosen per machine at setup (CPU by default in `setup.bat`, CUDA for NVIDIA, ROCm for AMD — ROCm exposes `torch.cuda`, so Laya needs no changes). Install the AMD ROCm PyTorch build on the dev machine (Radeon RX 7800 XT, gfx1101, Windows 11), confirming wheel availability for the `.venv` Python version (3.14; AMD Windows wheels historically targeted 3.12), and verify `laya.load` + `predict` run on the GPU with the fine-tuned checkpoint.
  - **Verification**: `torch.cuda.is_available()` is true on the AMD GPU and a checkpoint prediction matches the CPU result within autocast tolerance; document the install steps in the README.

- [ ] **TASK-20: Real-Document Validation & Regression Verification & Work-Unit Commit**
  - **Route**: direct inline
  - **Scope**: Run the full pytest suite across `src/`; manually validate results against real Silvina Editorial documents (not just the synthetic archetype test set).
  - **Verification**: Zero regressions; commit work-unit to `feat/laya-system-one-ports`.

---

## 4. Progress & Verification Log

- **Current Status**: Phase 2 Complete (TASK-06 through TASK-11 done; validated checkpoint at `data/laya/checkpoints/laya_finetuned_v1_16epochs/`). Phase 3 planned (TASK-12 through TASK-21 defined below), awaiting explicit user go-ahead to start TASK-12.
- **Next Step**: TASK-21 (Validate Laya GPU inference on AMD ROCm) / TASK-19 (Update AnalyzeDocumentUseCaseWiring). Smoke run of the fine-tuned checkpoint on CPU: load 11.6 s, one `decide` 25.5 s (see TASK-21 for GPU).
- **Data Location Decision**: The `E:\IA\laya` repository is kept clean (frequent upstream updates); all generated datasets and generation scripts were relocated to `data/laya/` inside `silvina-editorial` and are tracked in this repo (~12MB total).

### Verification History
- **TASK-01**: Complete.
  - RED: pytest collection failed with `ModuleNotFoundError: No module named 'src.domain.classification.research_intent_detector_port'`.
  - GREEN: Implemented `ResearchIntentDetectorPort` and `FakeResearchIntentDetectorPort`. 5 tests passed in `test_research_intent_detector_port.py`. Full suite: 690 passed.
  - Commit: `7bb93fa` (`feat(classification): define ResearchIntentDetectorPort and test double`).

- **TASK-02**: Complete.
  - RED: pytest collection failed with `ModuleNotFoundError: No module named 'src.infrastructure.adapters.classification.ollama_research_intent_adapter'`.
  - GREEN: Implemented `OllamaResearchIntentAdapter` fulfilling `ResearchIntentDetectorPort`. 5 tests passed in `test_ollama_research_intent_adapter.py`. Full suite: 695 passed.
  - Commit: `cc7644a` (`feat(classification): implement OllamaResearchIntentAdapter and unit tests`).

- **TASK-03**: Complete.
  - RED: Constructor mismatch and type error when attempting to instantiate with `research_intent_detector`.
  - GREEN: Refactored `ArticleClassifier` constructor and `classify` method. Removed direct dependencies on `LlmGeneratorPort`, prompt templates, and response parsers. 5 tests passed in `test_article_classifier_imryd_override.py`.
  - Commit: `803a7c1` (`feat(classification): refactor ArticleClassifier to depend on ResearchIntentDetectorPort`).

- **TASK-04**: Complete.
  - RED: Verified existing wiring tests failed due to attribute mismatch on `_article_classifier._llm_generator`.
  - GREEN: Added `_get_research_intent_detector(self) -> ResearchIntentDetectorPort` instantiating `OllamaResearchIntentAdapter`, updated `_get_article_classifier`, and updated wiring tests. All 15 tests in `test_analyze_document_use_case_wiring.py` passed. Full suite: 695 passed.
  - Commit: `ee560c1` (`feat(wiring): wire OllamaResearchIntentAdapter into AnalyzeDocumentUseCaseWiring`).

- **TASK-05**: Complete.
  - Verification: Full pytest suite across `src/` passed cleanly (695 passed, 1 warning, 17 subtests passed in 2.74s) with zero regressions.
  - Commit: `682479f` (`docs(odd): complete TASK-05 regression verification and close phase 1`).

- **TASK-06**: Complete.
  - Verification: Generated `archetypes_specification.json` defining the 56 archetypes (7 defense lines x 8 boolean profiles) with realistic subthemes and ground truth. Automated integrity test passed asserting 56 distinct archetypes, 7 lines, and 8 profiles per line.
  - Commit: `ffd2cc8` (silvina-editorial) / `8b6a4af` (laya: `feat(data): define 56-archetype combinatorial matrix specification for defense domain`).

- **TASK-07**: Complete.
  - Verification: Implemented `generate_full_dataset.py` with batch filtering, schema validation, and word range calibration. Executed test batch on Line 1 (16 samples) verifying word count range [1034, 1141] and 100% schema compliance.
  - Commit: `faf9b3f` (silvina-editorial) / `bdefc7a` (laya: `feat(scripts): implement batch synthetic dataset generator and validator for Laya`).

- **TASK-08**: Complete.
  - Verification: Generated full dataset of 480 samples in `data/silvina_editorial/dataset_raw.jsonl` (448 defense samples across 56 archetypes + 32 out-of-domain control samples). Automated validation confirmed 480/480 valid samples, word count range [1033, 1141] (average 1111.3 words), and 100% schema compliance.
  - Commit: `50c2e28` (silvina-editorial) / `b0342c8` (laya: `chore(data): exclude raw jsonl datasets from git and untrack pilot samples`).

- **TASK-09**: Complete.
  - Verification: Created `split_dataset.py` with seed=42 executing stratified split: `train.jsonl` (384 samples, 80%), `calibration.jsonl` (48 samples, 10%), `test.jsonl` (48 samples, 10%). Automated validation passed across all 3 files (0 errors, word range [1033, 1141], zero data leakage/overlap between splits).
  - Data relocation: `E:\IA\laya\data` and its generation scripts were moved into `data/laya/` inside `silvina-editorial` (tracked, not gitignored) to keep the frequently-updated `laya` repository free of generated artifacts.
  - Commit: `409141b`.

- **TASK-10**: Complete.
  - Verification: Implemented `generate_gold_distributions.py`, sampling each `state`+`questions` against Ollama (`hf.co/unsloth/gemma-4-26B-A4B-it-GGUF:UD-IQ4_XS`) 5 times at temperature 0.7 to build empirical teacher probability distributions. Ran in small batches (~30 samples, ~15-20 min each) to avoid long unattended runs. Consolidated and validated `data/laya/gold/train_with_gold.jsonl` (384), `calibration_with_gold.jsonl` (48), `test_with_gold.jsonl` (48) — 480/480 records, all `gold` distributions sum to 1.0 across the 9 question ids.
  - Fixed a prompt bug where `choice`-type questions (e.g. `research_line`) only listed option keys without their descriptions, causing the model to guess blindly; fix included the criteria description per key.
  - Commit: `f84b646`.

- **TASK-11: Kaggle Fine-Tuning (Phase 2 completion)**
  - Route: subagent delegation (notebook adaptation) + direct inline (Kaggle CLI setup, training runs, diagnosis).
  - Uploaded `data/laya/gold/*.jsonl` as private Kaggle Dataset `vulturarg/silvina-editorial-laya-gold` (~6MB uncompressed).
  - Delegated adaptation of the fine-tuning notebook to `gentle-ai-worker` (via a temporary copy inside `silvina-editorial`, since the original lives in `E:\IA\laya`, a separate git repo outside this session's allowed edit surface): swapped the public `LocalLLaMA/typed-decisions` HF benchmark for our own dataset, built evaluation `gold` from `expected` (one-hot for `choice`, `{label, score}` for `score`), disabled HuggingFace Hub publish by default (`PUBLISH_TO_HUB = False`), and made per-workflow reporting dynamic.
  - **Data location decision (reaffirmed)**: `E:\IA\laya` is never modified, not even for code changes like notebook edits — all such adaptations live only in `silvina-editorial`. The adapted notebook is kept at `data/laya/notebooks/laya_finetune_typed_decisions_2xT4_kaggle.ipynb` (tracked); the original in `E:\IA\laya` was restored untouched after each local edit/test cycle.
  - Kaggle requires phone verification on the account to unlock real GPU/TPU allocation — `enable_gpu: true` silently falls back to 0 GPUs otherwise. `--accelerator gpuT4x2` is required explicitly on `kaggle kernels push` for the dual-T4 shape.
  - First run (4 epochs, default recipe): accuracy 44%, score MAE 4.95/10, within-1-level 0% against `expected`. Loss decreased cleanly each epoch (1.00→0.64→0.37→0.34) — not a training bug, just too few total gradient updates (~192) for our ~10x-smaller-than-reference dataset.
  - Second run (16 epochs): `choice`-type metrics improved substantially (soft accuracy 77%→92%, Brier 0.36→0.14), but `score`-type metrics against `expected` barely moved (MAE 4.95→4.62, within-1-level stayed 0%).
  - Added a diagnostic comparison in the evaluation cell (`gold_teacher`, built from the teacher's own `gold` distribution) run alongside the existing `expected`-based comparison. Third run (16 epochs) confirmed the real cause: **against the teacher, Laya scores 86.6% accuracy, 0.39 score MAE, 95.3% within-1-level** — essentially matching the reference benchmark's own published numbers. The earlier poor scores were an artifact of comparing against `expected` (the archetype's synthetic, formula-derived ground truth used only to guarantee dataset diversity), not a training failure. Laya successfully learned to imitate the teacher (Ollama), which is the actual architectural goal (replace Ollama's System 2 judgment with a fast System 1 engine).
  - Decision: `expected` is retired as an evaluation yardstick going forward; the teacher's `gold` distribution is the correct reference, since it is what Laya is meant to reproduce.
  - Checkpoint saved locally (not committed — no git-lfs) at `data/laya/checkpoints/laya_finetuned_v1_16epochs/` (~808MB), added to `.gitignore`.
  - Commit: Pending user instruction (held).

### Phase 3 Architecture Decision (recorded, not yet implemented)
- A single `LayaDecisionPort.decide(text_sample) -> LayaDecisionResultDTO` is invoked once per document (one Laya forward pass resolves all 9 questions), and the resulting DTO is threaded down into `ArticleClassifier`, `QualityAnalyzer`, and `EditorialSuitabilityAnalyzer` instead of each service calling Laya independently.
- Ollama stays wired for narrative text only, gated on demand: quality dimension feedback below 7.0 (`QualityLevel.GOOD` threshold), and editorial contribution/alignment narrative when the verdict is not the positive one.
- Laya's training `state` was near-complete document text (~1000-1200 words / ~7500 chars), not an excerpt built by either existing text sampler — TASK-13 introduces a dedicated sampler for Laya's `state` input.
- See TASK-12 through TASK-20 above for the full breakdown. Held pending explicit user instruction to start TASK-12.
