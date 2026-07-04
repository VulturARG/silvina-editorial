# Technical Design: Resolve Domain Vocabulary Enums Debt

## Technical Approach
We will refactor the internal member names (keys) of the Spanish `ArticleType` enum to English in order to satisfy the English-only identifier guidelines, while keeping its Spanish string values intact.
Specifically:
- In `ArticleType` ([article_type.py](file:///E:/Python/silvina-editorial/src/domain/enums/article_type.py)), `CIENTIFICO` and `DIVULGACION` will be renamed to `SCIENTIFIC` and `POPULAR_SCIENCE`.
- The string values of these enum members (e.g., `"científico"`) remain unchanged to ensure backwards compatibility with serialized outputs, CLI arguments, docx exports, and report formatting.
- All references in domain classifiers, rule tables, DTOs, required section providers, use cases, and tests will be systematically updated.

## Architecture Decisions
1. **Member-Only Translation (Value Preservation)**: Keeping the underlying string values exactly as-is ensures that serialization, CLI options, document parser outputs, and report generation behavior are not broken.
2. **`SectionType` explicitly OUT OF SCOPE (superseded)**: The original design proposed renaming `SectionType`'s Spanish members to distinct English synonyms (`RESUMEN` -> `SUMMARY`, `INTRODUCCION` -> `INTRO`, etc.) to avoid colliding with existing English members like `ABSTRACT`/`INTRODUCTION`. This was reverted: `SectionType` is intentionally **bilingual** — `RESUMEN`/`ABSTRACT`, `INTRODUCCION`/`INTRODUCTION`, etc. are deliberate parallel language variants of the same section, not Spanish-identifier debt. Renaming them to English synonyms would erase that bilingual intent. `section_type.py` and `test_section_type.py` are left fully unchanged.

## File Changes
The following files will be modified:

### 1. Enums Definitions
- [src/domain/enums/article_type.py](file:///E:/Python/silvina-editorial/src/domain/enums/article_type.py): Rename `CIENTIFICO` -> `SCIENTIFIC` and `DIVULGACION` -> `POPULAR_SCIENCE`.
- [src/domain/enums/classification_confidence.py](file:///E:/Python/silvina-editorial/src/domain/enums/classification_confidence.py): Update docstring reference from `CIENTIFICO` to `SCIENTIFIC`.
- [domain/enums.py](file:///E:/Python/silvina-editorial/domain/enums.py) *(Legacy)*: Out of scope. Kept unchanged with its Spanish keys — it is an independent enum definition, not imported by `src/`, so it does not need to track this rename.
- [src/domain/enums/section_type.py](file:///E:/Python/silvina-editorial/src/domain/enums/section_type.py): Out of scope (superseded) — bilingual by design, left unchanged.

### 2. Domain & Application Code
- [src/domain/classification/article_classifier.py](file:///E:/Python/silvina-editorial/src/domain/classification/article_classifier.py): Update `ArticleType.CIENTIFICO` to `ArticleType.SCIENTIFIC`.
- [src/domain/classification/classification_rule_table.py](file:///E:/Python/silvina-editorial/src/domain/classification/classification_rule_table.py): Update `ArticleType.CIENTIFICO` and `ArticleType.DIVULGACION` to their English member names.
- [src/domain/dtos/classification_result_dto.py](file:///E:/Python/silvina-editorial/src/domain/dtos/classification_result_dto.py): Update references in `effective_structure_type`.
- [src/domain/structure/required_sections_provider.py](file:///E:/Python/silvina-editorial/src/domain/structure/required_sections_provider.py): Update checks for `ArticleType.SCIENTIFIC` and `ArticleType.POPULAR_SCIENCE`.

### 3. Unit Tests
- [src/domain/tests/enums/test_article_type.py](file:///E:/Python/silvina-editorial/src/domain/tests/enums/test_article_type.py): Update assertions to verify renamed keys.
- [src/domain/tests/enums/test_section_type.py](file:///E:/Python/silvina-editorial/src/domain/tests/enums/test_section_type.py): Out of scope (superseded) — left unchanged.
- [src/domain/tests/classification/test_article_classifier_imryd_override.py](file:///E:/Python/silvina-editorial/src/domain/tests/classification/test_article_classifier_imryd_override.py): Update to `ArticleType.SCIENTIFIC`.
- [src/domain/tests/classification/test_classification_rule_table_cientifico.py](file:///E:/Python/silvina-editorial/src/domain/tests/classification/test_classification_rule_table_cientifico.py): Rename file to `test_classification_rule_table_scientific.py` and update test class/member references.
- [src/domain/tests/classification/test_classification_rule_table_divulgacion_near_miss.py](file:///E:/Python/silvina-editorial/src/domain/tests/classification/test_classification_rule_table_divulgacion_near_miss.py): Rename to `test_classification_rule_table_popular_science_near_miss.py` and update references.
- [src/domain/tests/classification/test_classification_rule_table_divulgacion_standard.py](file:///E:/Python/silvina-editorial/src/domain/tests/classification/test_classification_rule_table_divulgacion_standard.py): Rename to `test_classification_rule_table_popular_science_standard.py` and update references.
- [src/domain/tests/classification/test_rule_case.py](file:///E:/Python/silvina-editorial/src/domain/tests/classification/test_rule_case.py): Update references.
- [src/domain/tests/dtos/test_analysis_result.py](file:///E:/Python/silvina-editorial/src/domain/tests/dtos/test_analysis_result.py): Update references.
- [src/domain/tests/dtos/test_classification_result.py](file:///E:/Python/silvina-editorial/src/domain/tests/dtos/test_classification_result.py): Update references.
- [src/domain/tests/structure/test_required_sections_provider.py](file:///E:/Python/silvina-editorial/src/domain/tests/structure/test_required_sections_provider.py): Update references.
- [src/domain/tests/structure/test_structure_validator_cientifico.py](file:///E:/Python/silvina-editorial/src/domain/tests/structure/test_structure_validator_cientifico.py): Rename to `test_structure_validator_scientific.py` and update references.
- [src/domain/tests/structure/test_structure_validator_divulgacion.py](file:///E:/Python/silvina-editorial/src/domain/tests/structure/test_structure_validator_divulgacion.py): Rename to `test_structure_validator_popular_science.py` and update references.
- [src/application/tests/test_analyze_document_use_case.py](file:///E:/Python/silvina-editorial/src/application/tests/test_analyze_document_use_case.py): Update references.
- [src/application/tests/test_validate_structure_use_case.py](file:///E:/Python/silvina-editorial/src/application/tests/test_validate_structure_use_case.py): Update references.

### 4. Root Tests Referencing the New `src` Enum
Scope is restricted to `src/`. The legacy mirror ([domain/enums.py](file:///E:/Python/silvina-editorial/domain/enums.py)) and legacy business logic (`business_logic/article_classifier.py`, `business_logic/structure_validator.py`, `main_legacy.py`) keep their Spanish keys (`CIENTIFICO`, `DIVULGACION`) untouched — they are a separate, independent enum definition, not an import of `src.domain.enums`. Only root tests that import `ArticleType` from `src.domain.enums.article_type` are updated:
- [tests/test_main_cli_args.py](file:///E:/Python/silvina-editorial/tests/test_main_cli_args.py)
- [tests/test_main_dto_mapping.py](file:///E:/Python/silvina-editorial/tests/test_main_dto_mapping.py)
- [tests/e2e/test_gradio_e2e.py](file:///E:/Python/silvina-editorial/tests/e2e/test_gradio_e2e.py)
- [tests/smoke/test_validate_structure_parity.py](file:///E:/Python/silvina-editorial/tests/smoke/test_validate_structure_parity.py): only the references to the new `ArticleType` (imported from `src`) are renamed; `LegacyArticleType` (imported from `domain.enums`) keeps its Spanish keys, since this test compares both enums side by side.

`tests/legacy/test_article_classifier.py` and `tests/legacy/test_structure_validator.py` exercise only the legacy `business_logic` path and are unaffected — left unchanged.

## Testing Strategy
1. **Unit Test Updates**: Update the assertions, file names, and class names of tests that target the renamed enums.
2. **Regression Testing**: Execute the test suite via `.venv\Scripts\pytest` to verify that all 641 tests continue to pass and no internal references are broken.
3. **Parity Testing**: Run the structure validation and classification parity smoke tests to verify legacy and clean-architecture components produce identical outputs.
