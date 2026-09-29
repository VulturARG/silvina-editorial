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

- [ ] **TASK-08: Generate Full Dataset (~450-500 samples)**
  - **Route**: subagent delegation / batch execution
  - **Scope**: Generate complete dataset covering all 56 archetypes plus out-of-domain controls.
  - **Verification**: Line count, word count distribution, and JSONL format validation.

- [ ] **TASK-09: Stratified Partitioning (Train / Calibration / Test)**
  - **Route**: direct inline
  - **Scope**: Split raw dataset into `train.jsonl` (80%), `calibration.jsonl` (10%), and `test.jsonl` (10%) with balanced representation across archetypes.
  - **Verification**: Assert non-overlapping splits, seed reproducibility, and calibration holdout integrity.

---

## 4. Progress & Verification Log

- **Current Status**: In Progress (Phase 2: TASK-07 complete; ready for TASK-08)
- **Next Step**: Awaiting user approval to proceed with TASK-08 (Generate Full Dataset)

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
  - Commit: Pending user instruction (held).
