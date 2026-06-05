# Structure Validation Specification

## Purpose

This specification defines the structural validation requirements for academic manuscripts based on their classification category.

## Requirements

### Requirement: Scientific Article Structure Validation

The system MUST validate that a scientific article (`ArticleType.CIENTIFICO`) contains all the required sections: Resumen, Introducción, Metodología, Resultados, Discusión, Conclusiones, and Referencias.

#### Scenario: Compliant Scientific Article
- GIVEN a document containing sections labeled "Resumen", "Introducción", "Metodología", "Resultados", "Discusión", "Conclusiones", and "Referencias"
- WHEN the structure is validated for a scientific article
- THEN the validation MUST succeed with all sections marked present

#### Scenario: Scientific Article Missing Methodology
- GIVEN a document containing sections labeled "Resumen", "Introducción", "Resultados", "Discusión", "Conclusiones", and "Referencias" (missing "Metodología")
- WHEN the structure is validated for a scientific article
- THEN the validation MUST fail and report "Metodología" as a missing section

#### Scenario: Scientific Article with Variant Names
- GIVEN a document containing sections labeled "Abstract", "Introduction", "Materiales y métodos", "Findings", "Discussion", "Conclusión", and "Bibliografía"
- WHEN the structure is validated for a scientific article
- THEN the validation MUST succeed with all sections marked present
