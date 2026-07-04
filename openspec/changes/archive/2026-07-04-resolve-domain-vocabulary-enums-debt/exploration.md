## Exploration: resolve-domain-vocabulary-enums-debt

### Current State

The codebase contains three key domain enums under `src/domain/enums/` that define vocabulary for document analysis, classification, and validation. Some of these enums use Spanish identifiers (keys), which violates clean architecture guidelines requiring all identifiers to be in English.

1. **[quality_dimension.py](file:///E:/Python/silvina-editorial/src/domain/enums/quality_dimension.py)**
   - Members are already in English: `CLARITY`, `COHERENCE`, `ARGUMENTATION`, `CONCLUSIONS`.
   - String values are in Spanish: `"claridad"`, `"coherencia"`, `"argumentacion"`, `"conclusiones"`.
   - No key renaming is required here.

2. **[article_type.py](file:///E:/Python/silvina-editorial/src/domain/enums/article_type.py)**
   - Uses Spanish keys: `CIENTIFICO` and `DIVULGACION`.
   - Members/values:
     - `CIENTIFICO = "científico"`
     - `DIVULGACION = "divulgación"`
     - `OPINION = "opinión"`
     - `UNKNOWN = "unknown"`
   - Needs Spanish keys renamed to English while keeping string values intact.

3. **[section_type.py](file:///E:/Python/silvina-editorial/src/domain/enums/section_type.py)**
   - Contains a mix of English and Spanish keys, acting as duplicate entries for bilingual section types (e.g., `ABSTRACT` vs `RESUMEN`, `INTRODUCTION` vs `INTRODUCCION`).
   - Needs Spanish keys renamed to English, leading to potential naming collision with existing English keys for the same section categories.

---

### Affected Areas

#### 1. ArticleType Usages
- **Production Files**:
  - [article_type.py](file:///E:/Python/silvina-editorial/src/domain/enums/article_type.py) (Definition)
  - [validate_structure_use_case.py](file:///E:/Python/silvina-editorial/src/application/validate_structure_use_case.py) (Type hinting)
  - [article_classifier.py](file:///E:/Python/silvina-editorial/src/domain/classification/article_classifier.py) (Default classification mapping)
  - [classification_rule_table.py](file:///E:/Python/silvina-editorial/src/domain/classification/classification_rule_table.py) (Rule outcomes)
  - [rule_case.py](file:///E:/Python/silvina-editorial/src/domain/classification/rule_case.py) (DTO field)
  - [classification_result_dto.py](file:///E:/Python/silvina-editorial/src/domain/dtos/classification_result_dto.py) (Properties and types)
  - [required_sections_provider.py](file:///E:/Python/silvina-editorial/src/domain/structure/required_sections_provider.py) (Required sections mappings)

- **Test Files**:
  - [test_article_type.py](file:///E:/Python/silvina-editorial/src/domain/tests/enums/test_article_type.py)
  - [test_analyze_document_use_case.py](file:///E:/Python/silvina-editorial/src/application/tests/test_analyze_document_use_case.py)
  - [test_validate_structure_use_case.py](file:///E:/Python/silvina-editorial/src/application/tests/test_validate_structure_use_case.py)
  - [test_article_classifier_imryd_override.py](file:///E:/Python/silvina-editorial/src/domain/tests/classification/test_article_classifier_imryd_override.py)
  - [test_classification_rule_table_cientifico.py](file:///E:/Python/silvina-editorial/src/domain/tests/classification/test_classification_rule_table_cientifico.py)
  - [test_classification_rule_table_divulgacion_near_miss.py](file:///E:/Python/silvina-editorial/src/domain/tests/classification/test_classification_rule_table_divulgacion_near_miss.py)
  - [test_classification_rule_table_divulgacion_standard.py](file:///E:/Python/silvina-editorial/src/domain/tests/classification/test_classification_rule_table_divulgacion_standard.py)
  - [test_classification_rule_table_opinion.py](file:///E:/Python/silvina-editorial/src/domain/tests/classification/test_classification_rule_table_opinion.py)
  - [test_rule_case.py](file:///E:/Python/silvina-editorial/src/domain/tests/classification/test_rule_case.py)
  - [test_analysis_result.py](file:///E:/Python/silvina-editorial/src/domain/tests/dtos/test_analysis_result.py)
  - [test_classification_result.py](file:///E:/Python/silvina-editorial/src/domain/tests/dtos/test_classification_result.py)
  - [test_required_sections_provider.py](file:///E:/Python/silvina-editorial/src/domain/tests/structure/test_required_sections_provider.py)
  - [test_structure_validator_cientifico.py](file:///E:/Python/silvina-editorial/src/domain/tests/structure/test_structure_validator_cientifico.py)
  - [test_structure_validator_divulgacion.py](file:///E:/Python/silvina-editorial/src/domain/tests/structure/test_structure_validator_divulgacion.py)
  - [test_structure_validator_opinion.py](file:///E:/Python/silvina-editorial/src/domain/tests/structure/test_structure_validator_opinion.py)

#### 2. SectionType Usages
- **Production Files**:
  - [section_type.py](file:///E:/Python/silvina-editorial/src/domain/enums/section_type.py) (Definition)
  - [section_dto.py](file:///E:/Python/silvina-editorial/src/domain/dtos/section_dto.py) (Field type)
- **Test Files**:
  - [test_section_type.py](file:///E:/Python/silvina-editorial/src/domain/tests/enums/test_section_type.py) (Checks existence of Spanish keys: `RESUMEN`, `INTRODUCCION`, `METODOLOGIA`, `CONCLUSIONES`, `REFERENCIAS`)
  - [test_section.py](file:///E:/Python/silvina-editorial/src/domain/tests/dtos/test_section.py) (Sets and asserts on `SectionType.INTRODUCTION`)

---

### Approaches

#### 1. ArticleType Renaming
The goal is to rename:
- `CIENTIFICO` -> `SCIENTIFIC`
- `DIVULGACION` -> `POPULAR_SCIENCE`

Other options considered for `DIVULGACION`:
- **Option A: POPULAR_SCIENCE** (Recommended): standard translation of "divulgación científica" in research environments.
- **Option B: OUTREACH**: common for institutional outreach, but lacks focus on science/academic article categories.
- **Option C: DIVULGATION**: literal translation, but less idiomatic in English.

#### 2. SectionType Spanish Keys Mapping Options
Because `SectionType` contains parallel English/Spanish pairs representing similar sections in different languages (e.g. `ABSTRACT` and `RESUMEN`), we cannot map `RESUMEN` directly to `ABSTRACT` without name collision. We need distinct English keys.

- **Option A (Suffixing)**:
  Append a `_SPANISH` suffix to all Spanish section types.
  - `RESUMEN` -> `ABSTRACT_SPANISH = "resumen"`
  - `PALABRAS_CLAVE` -> `KEYWORDS_SPANISH = "palabras_clave"`
  - `INTRODUCCION` -> `INTRODUCTION_SPANISH = "introduccion"`
  - `METODOLOGIA` -> `METHODOLOGY_SPANISH = "metodologia"`
  - `RESULTADOS` -> `RESULTS_SPANISH = "resultados"`
  - `DISCUSION` -> `DISCUSSION_SPANISH = "discusion"`
  - `CONCLUSIONES` -> `CONCLUSIONS_SPANISH = "conclusiones"`
  - `REFERENCIAS` -> `REFERENCES_SPANISH = "referencias"`
  - `BIBLIOGRAFIA` -> `BIBLIOGRAPHY_SPANISH = "bibliografia"`
  - `AGRADECIMIENTOS` -> `ACKNOWLEDGMENTS_SPANISH = "agradecimientos"`
  - `ANEXO` -> `APPENDIX_SPANISH = "anexo"`

- **Option B (Prefixing)**:
  Prepend a `SPANISH_` prefix to all Spanish section types.
  - `RESUMEN` -> `SPANISH_ABSTRACT = "resumen"`
  - `PALABRAS_CLAVE` -> `SPANISH_KEYWORDS = "palabras_clave"`
  - etc.

- **Comparison**:
  Option A (Suffixing) is superior as it groups similar section types together alphabetically (e.g. `ABSTRACT` and `ABSTRACT_SPANISH` are kept adjacent), improving autocompletion usability and code readability.

---

### Recommendation

1. Keep `QualityDimension` keys unchanged (already English).
2. Rename `ArticleType` members:
   - `CIENTIFICO` -> `SCIENTIFIC`
   - `DIVULGACION` -> `POPULAR_SCIENCE`
3. Rename `SectionType` Spanish members using suffixing:
   - `RESUMEN` -> `ABSTRACT_SPANISH`
   - `PALABRAS_CLAVE` -> `KEYWORDS_SPANISH`
   - `INTRODUCCION` -> `INTRODUCTION_SPANISH`
   - `METODOLOGIA` -> `METHODOLOGY_SPANISH`
   - `RESULTADOS` -> `RESULTS_SPANISH`
   - `DISCUSION` -> `DISCUSSION_SPANISH`
   - `CONCLUSIONES` -> `CONCLUSIONS_SPANISH`
   - `REFERENCIAS` -> `REFERENCES_SPANISH`
   - `BIBLIOGRAFIA` -> `BIBLIOGRAPHY_SPANISH`
   - `AGRADECIMIENTOS` -> `ACKNOWLEDGMENTS_SPANISH`
   - `ANEXO` -> `APPENDIX_SPANISH`
4. Update all test assertions and production references accordingly.

---

### Risks

- **Internal references**: Missed occurrences in rule tables or DTO validation tests could break classification logic. However, since the test suite provides 100% coverage over these rule paths, running the test suite after the refactor will immediately catch any missing updates.
- **External integration**: Since all string values (values of the enum members) remain exactly as they were (e.g., `ArticleType.SCIENTIFIC.value` continues to be `"científico"`), serialization/deserialization logic is completely unaffected.

---

### Ready for Proposal
Yes
