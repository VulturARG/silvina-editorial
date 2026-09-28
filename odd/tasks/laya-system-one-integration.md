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

- [ ] **TASK-02: Implement `OllamaResearchIntentAdapter`**
  - **Route**: direct inline
  - **Scope**: Create `src/infrastructure/adapters/classification/ollama_research_intent_adapter.py` implementing `ResearchIntentDetectorPort` by delegating to `LlmGeneratorPort`, prompt template rendering, and `ArticleClassificationResponseParser`.
  - **Verification**: Unit tests in `src/infrastructure/tests/adapters/classification/test_ollama_research_intent_adapter.py`.

- [ ] **TASK-03: Refactor `ArticleClassifier` to depend on `ResearchIntentDetectorPort`**
  - **Route**: direct inline
  - **Scope**: Update `src/domain/classification/article_classifier.py` constructor to receive `research_intent_detector: ResearchIntentDetectorPort` instead of `llm_generator`, `signal_prompt_template`, `temperature`, `num_predict`, and `response_parser`.
  - **Verification**: Update `src/domain/tests/classification/test_article_classifier.py` with a fake test double implementing `ResearchIntentDetectorPort`.

- [ ] **TASK-04: Update `AnalyzeDocumentUseCaseWiring`**
  - **Route**: direct inline
  - **Scope**: Update `src/infrastructure/wirings/analyze_document_use_case_wiring.py` method `_get_article_classifier()` to instantiate `OllamaResearchIntentAdapter` and inject it.
  - **Verification**: Test wiring and integration in `src/infrastructure/tests/wirings/test_analyze_document_use_case_wiring.py` or existing wiring tests.

- [ ] **TASK-05: Regression Verification & Work-Unit Commit**
  - **Route**: direct inline
  - **Scope**: Run full pytest suite across `src/` (685+ tests). Ensure zero regressions.
  - **Verification**: Commit work-unit to `feat/laya-system-one-ports`.

---

## 4. Progress & Verification Log

- **Current Status**: In Progress (TASK-01 complete; ready for TASK-02)
- **Next Step**: Awaiting user approval to proceed with TASK-02 (Implement `OllamaResearchIntentAdapter`)

### Verification History
- **TASK-01**: Complete.
  - RED: pytest collection failed with `ModuleNotFoundError: No module named 'src.domain.classification.research_intent_detector_port'`.
  - GREEN: Implemented `ResearchIntentDetectorPort` and `FakeResearchIntentDetectorPort`. 5 tests passed in `test_research_intent_detector_port.py`. Full suite: 690 passed.
  - Commit: Pending user instruction (held).
