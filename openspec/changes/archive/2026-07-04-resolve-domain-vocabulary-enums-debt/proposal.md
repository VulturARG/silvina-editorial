# Proposal: Resolve Domain Vocabulary Enums Debt

## Intent
Resolve Domain Vocabulary Enums Debt by renaming enum keys in Spanish to English for `ArticleType` in `src/domain/enums/`.

## Scope
- Refactor `ArticleType` members in [article_type.py](file:///E:/Python/silvina-editorial/src/domain/enums/article_type.py):
  - `CIENTIFICO` -> `SCIENTIFIC`
  - `DIVULGACION` -> `POPULAR_SCIENCE`
- Keep string values exactly as they are currently in Spanish (no changes).
- Update references in domain models, DTOs, rule tables, use cases, and tests.
- Restricted to `src/`: the legacy `domain/enums.py` mirror, `business_logic/*`, `main_legacy.py`, and `tests/legacy/*` are out of scope (independent legacy enum, not imported by `src/`).
- `SectionType` ([section_type.py](file:///E:/Python/silvina-editorial/src/domain/enums/section_type.py)) is explicitly OUT OF SCOPE — its Spanish members (`RESUMEN`, `PALABRAS_CLAVE`, `INTRODUCCION`, `METODOLOGIA`, `RESULTADOS`, `DISCUSION`, `CONCLUSIONES`, `REFERENCIAS`, `BIBLIOGRAFIA`, `AGRADECIMIENTOS`, `ANEXO`) are intentionally bilingual pairs (e.g. `ABSTRACT`/`RESUMEN`) representing distinct language variants of the same section, not translation debt — left unchanged.

## Approach
1. **Refactor `ArticleType` Enum**: Rename `CIENTIFICO` to `SCIENTIFIC` and `DIVULGACION` to `POPULAR_SCIENCE` in `src/domain/enums/article_type.py`. Keep string values intact.
2. **Update Codebase References**: Use multi-file replacement to update all references to the renamed enum members in `src/domain/classification/article_classifier.py`, `src/domain/classification/classification_rule_table.py`, `src/domain/dtos/classification_result_dto.py`, `src/domain/structure/required_sections_provider.py`, and use case files.
3. **Update Tests**: Adjust all references in application and domain tests including `test_article_type.py`, all rule table and structure validator tests, and the root tests that import the new `src` `ArticleType`.
4. **Verification**: Run `.venv\Scripts\pytest` to verify all 641 tests pass cleanly.

## Capabilities
### New Capabilities
None

### Modified Capabilities
None
