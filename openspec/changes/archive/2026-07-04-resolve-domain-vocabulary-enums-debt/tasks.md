# Implementation Tasks: Resolve Domain Vocabulary Enums Debt

```text
Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: stacked-to-main
400-line budget risk: Low
```

## Phase 1: Foundation (Updating enums and mapping definitions)
- [x] Refactor [article_type.py](file:///E:/Python/silvina-editorial/src/domain/enums/article_type.py):
  - Rename `CIENTIFICO` -> `SCIENTIFIC` and `DIVULGACION` -> `POPULAR_SCIENCE`.
  - Keep string values `"científico"` and `"divulgación"` unchanged.
- [x] Out of scope (superseded): [section_type.py](file:///E:/Python/silvina-editorial/src/domain/enums/section_type.py) left unchanged — `SectionType`'s Spanish members are intentional bilingual pairs (e.g. `RESUMEN`/`ABSTRACT`), not translation debt.
- [x] Update docstring references in [classification_confidence.py](file:///E:/Python/silvina-editorial/src/domain/enums/classification_confidence.py).
- [x] Out of scope: [domain/enums.py](file:///E:/Python/silvina-editorial/domain/enums.py) (legacy) left unchanged — scope restricted to `src/`; it's an independent enum, not imported by `src/`.

## Phase 2: Core Refactoring (Enum translation)
- [x] Update references in [article_classifier.py](file:///E:/Python/silvina-editorial/src/domain/classification/article_classifier.py):
  - Change `ArticleType.CIENTIFICO` -> `ArticleType.SCIENTIFIC`.
- [x] Update references in [classification_rule_table.py](file:///E:/Python/silvina-editorial/src/domain/classification/classification_rule_table.py):
  - Translate all instances of `ArticleType.CIENTIFICO`/`DIVULGACION` to `SCIENTIFIC`/`POPULAR_SCIENCE`.
- [x] Update references in [classification_result_dto.py](file:///E:/Python/silvina-editorial/src/domain/dtos/classification_result_dto.py).
- [x] Update references in [required_sections_provider.py](file:///E:/Python/silvina-editorial/src/domain/structure/required_sections_provider.py).

## Phase 3: Infrastructure Wiring (Wiring & configuration updates)
- [x] Audit and update any references or imports in `src/infrastructure/wirings/` if applicable.

## Phase 4: Unit Test Alignment
- [x] Rename classification rule table test files and update their class/method names and enum references:
  - [test_classification_rule_table_cientifico.py](file:///E:/Python/silvina-editorial/src/domain/tests/classification/test_classification_rule_table_cientifico.py) -> `test_classification_rule_table_scientific.py`
  - [test_classification_rule_table_divulgacion_near_miss.py](file:///E:/Python/silvina-editorial/src/domain/tests/classification/test_classification_rule_table_divulgacion_near_miss.py) -> `test_classification_rule_table_popular_science_near_miss.py`
  - [test_classification_rule_table_divulgacion_standard.py](file:///E:/Python/silvina-editorial/src/domain/tests/classification/test_classification_rule_table_divulgacion_standard.py) -> `test_classification_rule_table_popular_science_standard.py`
- [x] Rename structure validator test files and update references:
  - [test_structure_validator_cientifico.py](file:///E:/Python/silvina-editorial/src/domain/tests/structure/test_structure_validator_cientifico.py) -> `test_structure_validator_scientific.py`
  - [test_structure_validator_divulgacion.py](file:///E:/Python/silvina-editorial/src/domain/tests/structure/test_structure_validator_divulgacion.py) -> `test_structure_validator_popular_science.py`
- [x] Update assertions and enum references in the following domain test files:
  - [test_article_type.py](file:///E:/Python/silvina-editorial/src/domain/tests/enums/test_article_type.py)
  - [test_article_classifier_imryd_override.py](file:///E:/Python/silvina-editorial/src/domain/tests/classification/test_article_classifier_imryd_override.py)
  - [test_rule_case.py](file:///E:/Python/silvina-editorial/src/domain/tests/classification/test_rule_case.py)
  - [test_analysis_result.py](file:///E:/Python/silvina-editorial/src/domain/tests/dtos/test_analysis_result.py)
  - [test_classification_result.py](file:///E:/Python/silvina-editorial/src/domain/tests/dtos/test_classification_result.py)
  - [test_required_sections_provider.py](file:///E:/Python/silvina-editorial/src/domain/tests/structure/test_required_sections_provider.py)
- [x] Update assertions and enum references in the application use case test files:
  - [test_analyze_document_use_case.py](file:///E:/Python/silvina-editorial/src/application/tests/test_analyze_document_use_case.py)
  - [test_validate_structure_use_case.py](file:///E:/Python/silvina-editorial/src/application/tests/test_validate_structure_use_case.py)
- [x] Update root `tests/` that reference the new `src` `ArticleType` (only, since scope is restricted to `src/`):
  - [test_main_cli_args.py](file:///E:/Python/silvina-editorial/tests/test_main_cli_args.py)
  - [test_main_dto_mapping.py](file:///E:/Python/silvina-editorial/tests/test_main_dto_mapping.py)
  - [test_gradio_e2e.py](file:///E:/Python/silvina-editorial/tests/e2e/test_gradio_e2e.py)
  - [test_validate_structure_parity.py](file:///E:/Python/silvina-editorial/tests/smoke/test_validate_structure_parity.py): only the `ArticleType` (new, src) side; `LegacyArticleType` kept in Spanish.
- [x] Out of scope: [test_article_classifier.py](file:///E:/Python/silvina-editorial/tests/legacy/test_article_classifier.py) and [test_structure_validator.py](file:///E:/Python/silvina-editorial/tests/legacy/test_structure_validator.py) exercise only the legacy `business_logic` path — left unchanged.

## Phase 5: Verification (Run pytest, verify CLI output)
- [x] Execute the test suite using pytest to verify that all 641 tests pass.
- [ ] Manually verify that CLI and gradio app still work correctly.
