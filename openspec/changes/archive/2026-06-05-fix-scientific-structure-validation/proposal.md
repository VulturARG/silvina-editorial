# Proposal: Fix Scientific Structure Validation

## Intent

Scientific articles (`CIENTIFICO`) require the sections "Metodología", "Resultados", and "Discusión" to be present. However, the structure validator's extraction map (`section_map`) lacks entries for these sections, causing the validator to always flag them as missing. This proposal adds the necessary mappings so scientific articles can be validated correctly.

## Scope

### In Scope
- Update `section_map` in `business_logic/structure_validator.py` to include mappings for:
  - `metodología`
  - `resultados`
  - `discusión`
- Map these new sections to common Spanish and English variants (e.g. "methodology", "results", "discussion").

### Out of Scope
- Modifying the list of required sections per article type.
- Creating an automated test runner or suite (out of scope for this simple bug fix slice).

## Capabilities

### New Capabilities
None

### Modified Capabilities
None

## Approach

We will modify the `section_map` dictionary in `business_logic/structure_validator.py` to include the missing section keys and their corresponding keyword lists:
```python
            'metodología': ['metodología', 'metodologia', 'methodology', 'método', 'metodo', 'materiales y métodos'],
            'resultados': ['resultados', 'resultados y análisis', 'results'],
            'discusión': ['discusión', 'discusion', 'discussion']
```
Since these names capitalized match the required sections (e.g. `"metodología".capitalize() == "Metodología"`), this will align perfectly with the required sections list in `validate_structure`.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `business_logic/structure_validator.py` | Modified | Add `metodología`, `resultados`, and `discusión` to `section_map`. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| False matching of body paragraphs as section headers | Low | The validator already filters for paragraphs with short lengths (< 100 chars) or inline colon suffixes, which restricts matches to actual header candidates. |

## Rollback Plan

Revert changes using git:
```bash
git checkout business_logic/structure_validator.py
```

## Dependencies

None

## Success Criteria

- [ ] A scientific article containing sections labeled "Metodología", "Resultados", and "Discusión" (or their mapped variants) is successfully parsed, and these sections are no longer reported as missing.
