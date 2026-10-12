# Delta Spec — validate-structure

**Change**: validate-structure
**Phase**: spec
**Date**: 2026-06-15
**Status**: active

---

## Scope

What must be true after this change is applied. This spec covers the behavioral contracts for
the domain service, use case, wiring factory, and test suites introduced by the validate-structure
slice. It does NOT describe implementation details — only observable behavior.

---

## 1. Domain Service — StructureValidator

### 1.1 Section Aliases (behavioral-critical)

`StructureValidator` detects section headers with the aliases in `structure_norms.section_aliases`. That field is a `dict[SectionName, tuple[str, ...]]` built from the `[section_aliases]` table of `editorial_norms.toml` (see section 4.1). The keys are `SectionName` values and the loader lowercases the aliases. Every section listed in `[required_sections]` MUST have an entry in `[section_aliases]`; the loader rejects the file otherwise.

The values shipped in `editorial_norms.toml` are:

| Section | Aliases, in file order |
|---|---|
| `Resumen` | `resumen`, `abstract` |
| `Introducción` | `introducción`, `introduccion`, `introduction` |
| `Metodología` | `metodología`, `metodologia`, `methodology` |
| `Resultados` | `resultados`, `results` |
| `Discusión` | `discusión`, `discusion`, `discussion` |
| `Argumentación` | `argumentación`, `argumentacion`, `argumentation` |
| `Desarrollo` | `desarrollo`, `development` |
| `Conclusiones` | `conclusiones`, `conclusión`, `conclusion` |
| `Referencias` | `referencias`, `bibliografía`, `bibliografia`, `fuentes bibliográficas` |

**Order matters**: the first section whose alias matches wins, so the order of the `[section_aliases]` entries is part of the behavior. The table is a reading aid; the file is the source of truth.

### 1.2 Header Detection Rule

A paragraph from `DocumentContent.paragraphs` qualifies as a section header when EITHER of the
following conditions is true:

1. `len(paragraph) < max_header_length` (short-header rule), OR
2. The paragraph (lowercased, stripped) starts with `{keyword}:` or `{keyword} :`
   for any keyword in any alias list in `structure_norms.section_aliases` (inline-header rule).

`StructureValidator` takes `max_header_length: int` and `structure_norms: StructureNormsDTO` as required constructor arguments; `max_header_length` has no default. The wiring passes `EnvConfig.structure_max_header_length`: the `STRUCTURE_MAX_HEADER_LENGTH` environment variable when it is set, otherwise `[structure] max_header_length` in `analysis_settings.toml` (100 in the shipped file).
Paragraphs of length >= `max_header_length` that do NOT match the inline-header pattern are NEVER treated as
section headers, even if they contain section keywords in body text.

When a paragraph qualifies as a header, the service searches it (case-insensitively) for
any keyword from each `structure_norms.section_aliases` entry. The first matching section is recorded
as the detected `SectionName`.

### 1.3 Required Sections per ArticleType

The required sections come from `[required_sections]` in `editorial_norms.toml`, loaded into
`structure_norms.required_sections` and looked up by `StructureValidator`. The table below is the
content shipped with that file. Each entry is a `SectionName` enum member, not a raw string.

| ArticleType        | Required sections (ordered)                                                              |
|--------------------|------------------------------------------------------------------------------------------|
| `CIENTIFICO`       | `[SUMMARY, INTRODUCTION, METHODOLOGY, RESULTS, DISCUSSION, CONCLUSIONS, REFERENCES]` (7) |
| `DIVULGACION`      | `[SUMMARY, INTRODUCTION, DEVELOPMENT, CONCLUSIONS, REFERENCES]` (5)                      |
| `OPINION`          | `[INTRODUCTION, ARGUMENTATION, CONCLUSIONS]` (3)                                         |
| `UNKNOWN`          | `[]` (empty — no sections required)                                                       |

**Domain invariant**: `SectionName.DEVELOPMENT` MUST NOT appear in the required sections for
`CIENTIFICO` or `OPINION`. It IS included for `DIVULGACION` (faithful port of legacy).
The use case removes it unconditionally from `missing_sections` (port of `main.py:230`).

### 1.4 Missing Sections Calculation

`validate(document_content: DocumentContent, article_type: ArticleType) -> tuple[list[SectionName], list[SectionName]]`

- Calls `_extract_present_sections(paragraphs)` → `list[SectionName]` of detected canonical sections.
- Compares against required sections (case-insensitive via `.lower()`): a section is missing if
  its lowercased value does not appear in the lowercased present list.
- Returns `(present_sections, missing_sections)` as a raw tuple.
- Does NOT apply `has_references` filtering — that is use-case responsibility.
- Does NOT build `StructureValidationResult` — that is also use-case responsibility.

### 1.5 Output

Returns `tuple[list[SectionName], list[SectionName]]`:
- `present_sections` — enum members detected in the document (unused by current use case: `_`)
- `missing_sections` — enum members required but not detected

---

## 2. Domain Service — StructureValidator (Enhanced)

### 2.1 Enhanced Method Signature

`StructureValidator` is enhanced to encapsulate the document empty guard and section post-filtering logic:

```python
def validate_structure(
    self,
    document_content: DocumentContentDTO,
    article_type: ArticleType,
    has_references: bool,
) -> StructureValidationResultDTO
```

### 2.2 Empty Document Guard

If `document_content.paragraphs` is empty, raise `DocumentEmpty` exception.

### 2.3 Domain Service Behavior

1. Calls `validate(document_content, article_type)` to get `(present, missing)` sections.
2. Filters the `missing` sections list:
   - Unconditionally remove `SectionName.DEVELOPMENT`.
   - Remove `SectionName.REFERENCES` if `has_references` is `True`.
3. Constructs and returns `StructureValidationResultDTO(is_valid=(len(filtered_missing) == 0), missing_sections=filtered_missing)`.

**Scenarios**:
- Empty paragraphs list raises DocumentEmpty
  - GIVEN a `DocumentContentDTO` with `paragraphs == []`
  - WHEN `validate_structure` is called
  - THEN it raises `DocumentEmpty` exception
- Post-filtering removes Development and conditionally removes References
  - GIVEN a scientific article missing `DEVELOPMENT` and `REFERENCES` sections
  - AND `has_references = True`
  - WHEN `validate_structure` is called
  - THEN both `DEVELOPMENT` and `REFERENCES` are omitted from the returned `missing_sections`
  - AND `is_valid` is computed based on the filtered list

---

## 3. Orchestration — AnalyzeDocumentUseCase._validate_structure()

### 3.1 Simplified Signature

The private method `AnalyzeDocumentUseCase._validate_structure` delegates directly to `StructureValidator.validate_structure` without local post-processing:

```python
def _validate_structure(
    self,
    document_content: DocumentContentDTO,
    article_type: ArticleType,
    has_references: bool,
) -> StructureValidationResultDTO
```

### 3.2 Behavior

1. Call `self._structure_validator.validate_structure(document_content, article_type, has_references)`.
2. Return the result directly.

**Scenario**: Orchestration delegates structure validation
- GIVEN a valid `DocumentContentDTO`, `article_type`, and `has_references`
- WHEN `_validate_structure` is called
- THEN it returns the `StructureValidationResultDTO` produced by `StructureValidator.validate_structure`

---

## 4. Wiring — AnalyzeDocumentUseCaseWiring._get_structure_validator()

### 4.1 Factory Behavior

`AnalyzeDocumentUseCaseWiring` MUST:
- Create the `StructureValidator` dependency in its own private `_get_structure_validator(self) -> StructureValidator` method.
- Inject it into `AnalyzeDocumentUseCase`'s constructor (not constructed inline inside `execute()`).
- Pass `max_header_length` from `EnvConfig.structure_max_header_length`, which reads the `STRUCTURE_MAX_HEADER_LENGTH` environment variable or, when it is not set, `[structure] max_header_length` in `analysis_settings.toml`.
- Pass `structure_norms` from the editorial norms: `EditorialNormsLoader` reads `editorial_norms.toml` from the project root (resolved from the wiring module as `parents[3]`), validates it, and the wiring passes its `structure` field. The norms are loaded once per wiring instance, and a missing or invalid file fails fast when the use case is created.

Pattern:
```python
class AnalyzeDocumentUseCaseWiring:
    def create_use_case(self) -> AnalyzeDocumentUseCase:
        return AnalyzeDocumentUseCase(
            ...,
            structure_validator=self._get_structure_validator(),
            ...,
        )

    def _get_structure_validator(self) -> StructureValidator:
        env_config = self._get_env_config()
        return StructureValidator(
            max_header_length=env_config.structure_max_header_length,
            structure_norms=self._get_editorial_norms().structure,
        )
```

### 4.2 No Infrastructure Dependencies

`StructureValidator` MUST depend only on domain types (an `int` and a `StructureNormsDTO`). It MUST NOT
import from `src.infrastructure`, any port interface, or any external library. Reading the file, looking up
the environment variable and building the DTO are wiring-layer work; the domain class receives plain values.

---

## 5. Package Structure

The following packages and files MUST exist after the change is applied:

```
src/
  domain/
    structure/
      __init__.py
      structure_validator.py
      required_sections_provider.py
    tests/
      structure/
        __init__.py
        test_structure_validator.py
  application/
    analyze_document_use_case.py    # _validate_structure() lives here
  infrastructure/
    wirings/
      __init__.py
      analyze_document_use_case_wiring.py    # _get_structure_validator() lives here
```

---

## 6. Acceptance Scenarios

### S-01: Scientific article with all sections — valid

```
Given a DocumentContent with paragraphs:
  ["Resumen: El resumen.", "Introducción: Intro.", "Metodología: Método.",
   "Resultados: Los resultados.", "Discusión: Discusión.", "Conclusiones: Conclusión.",
   "Referencias: Refs."]
And article_type = ArticleType.CIENTIFICO
When validate is called on the domain service
Then result.is_valid is True
And result.missing_sections == []
```

### S-02: Scientific article with all sections (inline colon format) — valid

```
Given a DocumentContent with paragraphs using "Section: content" format
  where all 7 CIENTIFICO sections appear as short inline-header paragraphs
And article_type = ArticleType.CIENTIFICO
When validate is called
Then result.is_valid is True
And result.missing_sections == []
```

### S-03: Scientific article missing Resumen — invalid

```
Given a DocumentContent without any "Resumen" or "Abstract" paragraph
And article_type = ArticleType.CIENTIFICO
When validate is called
Then result.is_valid is False
And "Resumen" is in result.missing_sections
```

### S-04: Divulgacion article with all required sections — valid

```
Given a DocumentContent with paragraphs:
  ["Resumen: ...", "Introducción: ...", "Desarrollo: ...", "Conclusiones: ...", "Referencias: ..."]
And article_type = ArticleType.DIVULGACION
When validate is called
Then result.is_valid is True
And result.missing_sections == []
```

### S-05: Divulgacion article missing Desarrollo — invalid

```
Given a DocumentContent without any "Desarrollo" or "Development" paragraph
And article_type = ArticleType.DIVULGACION
When validate is called
Then result.is_valid is False
And "Desarrollo" is in result.missing_sections
```

### S-06: Opinion article with all required sections — valid

```
Given a DocumentContent with paragraphs:
  ["Introducción: ...", "Argumentación: ...", "Conclusiones: ..."]
And article_type = ArticleType.OPINION
When validate is called
Then result.is_valid is True
And result.missing_sections == []
```

### S-07: validate_structure returns StructureValidationResult object

```
Given a DocumentContent with any paragraphs
And article_type = ArticleType.DIVULGACION
When validate is called on the domain service
Then the return value has attribute is_valid (bool)
And the return value has attribute missing_sections (list)
```

### S-08: English alias "abstract" maps to canonical "Resumen"

```
Given a DocumentContent with paragraph "Abstract: This is the abstract."
When _extract_present_sections is called
Then "resumen" appears in the lowercased list of detected section names
```

### S-09: Multiple aliases resolved correctly (metodologia, methodology, discussion, results)

```
Given a DocumentContent with paragraphs:
  ["metodologia: Methods without accent.",
   "methodology: English version of methods.",
   "discussion: English version of discussion.",
   "results: English results."]
When _extract_present_sections is called
Then "metodología" appears in the lowercased detected sections
And "discusión" appears in the lowercased detected sections
And "resultados" appears in the lowercased detected sections
```

### S-10: Long body paragraph (>= 100 chars) is NOT detected as section header

```
Given a paragraph: "La introducción de nuevas metodologías en el campo de la investigación
  académica requiere un análisis." (len >= 100)
And it does NOT start with any keyword followed by ":"
When _extract_present_sections is called with this paragraph
Then result is []
```

### S-11: Short paragraph (< 100 chars) containing section keyword IS detected

```
Given a paragraph: "Introducción" (len < 100)
When _extract_present_sections is called
Then "Introducción" is in the returned list
```

### S-11b: Custom max_header_length threshold

```
Given a StructureValidator constructed with max_header_length = 50
And a paragraph of length 60: "Introducción de nuevas metodologías en el campo de..."
When _extract_present_sections is called with this paragraph
Then result is []
```

### S-12: Orchestrator raises DocumentEmpty on empty paragraphs list

```
Given a DocumentContentDTO where paragraphs == []
And article_type = ArticleType.CIENTIFICO
When AnalyzeDocumentUseCase._validate_structure() is called
Then DocumentEmpty is raised
And StructureValidator.validate is NOT called
```

### S-13: Orchestrator always removes "Desarrollo" from missing_sections

```
Given a DocumentContentDTO with paragraphs that contain all DIVULGACION sections
  EXCEPT "Desarrollo"
And article_type = ArticleType.DIVULGACION
And has_references = False
When AnalyzeDocumentUseCase._validate_structure() is called
Then "Desarrollo" is NOT in result.missing_sections
And result.is_valid is True
```

### S-14: Orchestrator with has_references=True removes "Referencias" from missing_sections

```
Given a DocumentContentDTO with paragraphs that contain all CIENTIFICO sections
  EXCEPT "Referencias"
And article_type = ArticleType.CIENTIFICO
And has_references = True
When AnalyzeDocumentUseCase._validate_structure() is called
Then "Referencias" is NOT in result.missing_sections
And result.is_valid is True
```

### S-15: Orchestrator with has_references=False does NOT remove "Referencias"

```
Given a DocumentContentDTO with paragraphs that contain all CIENTIFICO sections
  EXCEPT "Referencias"
And article_type = ArticleType.CIENTIFICO
And has_references = False
When AnalyzeDocumentUseCase._validate_structure() is called
Then "Referencias" IS in result.missing_sections
And result.is_valid is False
```

### S-15b: Domain service DOES report "Desarrollo" as missing (before orchestrator post-processing)

```
Given a DocumentContentDTO without any "Desarrollo" or "Development" paragraph
And article_type = ArticleType.DIVULGACION
When validate is called DIRECTLY on the domain service
Then "Desarrollo" IS in result.missing_sections
```

### S-16: UNKNOWN article type — no required sections, always valid

```
Given a DocumentContentDTO with any paragraphs (non-empty)
And article_type = ArticleType.UNKNOWN
When AnalyzeDocumentUseCase._validate_structure() is called
Then result.is_valid is True
And result.missing_sections == []
```

### S-16: DESARROLLO not required for CIENTIFICO

```
Given `structure_norms.required_sections[ArticleType.CIENTIFICO]` (loaded from `editorial_norms.toml`)
Then `SectionName.DEVELOPMENT` ("Desarrollo") is NOT in the returned tuple
```

### S-17: DESARROLLO not required for OPINION

```
Given `structure_norms.required_sections[ArticleType.OPINION]` (loaded from `editorial_norms.toml`)
Then `SectionName.DEVELOPMENT` ("Desarrollo") is NOT in the returned tuple
```

### S-18: "fuentes bibliográficas" alias maps to "Referencias"

```
Given a DocumentContent with paragraph "Fuentes bibliográficas: Autor, 2023."
When _extract_present_sections is called
Then "referencias" appears in the lowercased detected sections
```

### S-19: Wiring creates the domain service without errors

```
Given AnalyzeDocumentUseCaseWiring()._get_structure_validator() is called
Then the return value is an instance of StructureValidator
And its `max_header_length` is `EnvConfig.structure_max_header_length` (the `STRUCTURE_MAX_HEADER_LENGTH` variable, or 100 from `analysis_settings.toml`)
And no external adapters, ports, or infrastructure classes are imported
```

### S-20: StructureValidationResult is frozen (immutable after construction)

```
Given a StructureValidationResult returned by validate_structure
When an attempt is made to set any attribute on the result
Then a FrozenInstanceError (or equivalent dataclass frozen error) is raised
```

---

## 7. Legacy Test Coverage Mapping

The 10 tests in `tests/test_structure_validator.py` map to the following acceptance scenarios:

| Legacy test method                                  | Scenario(s) |
|-----------------------------------------------------|-------------|
| `test_scientific_article_detects_all_imryd_sections` | S-01, S-02  |
| `test_scientific_article_complete_is_valid`          | S-01        |
| `test_scientific_article_missing_resumen`            | S-03        |
| `test_divulgacion_article_compliant`                 | S-04        |
| `test_divulgacion_missing_desarrollo`                | S-05        |
| `test_opinion_article_complete_is_valid`             | S-06        |
| `test_validate_structure_returns_result_object`      | S-07        |
| `test_english_abstract_detected`                     | S-08        |
| `test_section_aliases_detected`                      | S-09        |
| `test_long_body_text_not_detected_as_section`        | S-10        |
| `test_short_section_header_is_detected`              | S-11        |

All 10 legacy tests MUST pass against the new domain service.
(The table lists 11 rows because S-01 covers two legacy tests.)

---

## 8. Constraints and Invariants

1. `_extract_present_sections` is a non-public method but MUST remain testable directly
   (legacy tests call it directly; it MUST NOT be renamed or made truly private via name mangling).
2. Comparison between detected sections and required sections is case-insensitive.
3. The domain service is stateless — no instance state is mutated across calls.
4. `StructureValidationResult` MUST be frozen (`frozen=True` dataclass). Use-case builds it once.
5. No new domain exception types are introduced. `DocumentEmpty` from `document_errors.py` is sufficient.
6. `StructureAnalyzer` is absorbed as internal logic. Its public `analyze()` method MUST NOT appear
   on the new domain service's public interface.
7. Legacy files (`business_logic/structure_validator.py`, `business_logic/structure_analyzer.py`,
   `main.py`) are NOT modified or deleted in this slice.
8. The 5-word filter from `StructureAnalyzer` is NOT used in the `validate_structure` path.
   Only the 100-character threshold applies.

---

## 9. Out of Scope

- Wiring the new use case into `main.py`
- Deleting any file under `business_logic/`
- Surfacing IMRyD signals (`has_introduction`, `has_methods`, etc.) in `StructureValidationResult`
- Creating `structure_errors.py` or any new exception type
- Infrastructure ports or adapters
- Using `DocumentContent.sections` dict instead of `paragraphs` list
- The `_get_required_sections(category: ClassificationCategory)` dead-code path in legacy

---

## 10. Input/Output Contracts

### Domain service inputs
- `document_content: DocumentContent` — scans `.paragraphs: list[str]`
- `article_type: ArticleType` — selects required section list

### Domain service output
- `StructureValidationResult(is_valid, missing_sections, section_details={}, timestamp=<auto>)`

### Orchestrator (`_validate_structure`) inputs
- `document_content: DocumentContentDTO`
- `article_type: ArticleType`
- `has_references: bool`

### Orchestrator (`_validate_structure`) output
- `StructureValidationResultDTO` with post-processing applied

### Exception
- `DocumentEmpty` raised when `document_content.paragraphs == []`
