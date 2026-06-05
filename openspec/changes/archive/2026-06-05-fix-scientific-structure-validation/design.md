# Design: Fix Scientific Structure Validation

## Technical Approach

We will extend the `section_map` dictionary in `StructureValidator._extract_present_sections` to map the required scientific article sections. This aligns extraction with validation requirements in `validate_structure`.

## Architecture Decisions

### Decision: Extend `section_map` in `StructureValidator`

**Choice**: Add the three scientific sections directly to `section_map`.
**Alternatives considered**: Creating a separate mapping system specifically for scientific documents.
**Rationale**: Modifying `section_map` keeps the extraction logic centralized and consistent. Since all matched sections are capitalized when added to the returned list (e.g. `section_name.capitalize()`), `'metodología'.capitalize()` yields `'Metodología'`, which matches the requirement string `'Metodología'` exactly.

## Data Flow

```
document_content.paragraphs 
   ──→ _extract_present_sections (checks section_map) 
   ──→ List of capitalized present sections (e.g., ["Resumen", "Metodología"]) 
   ──→ validate_structure (checks required list) 
   ──→ StructureValidationResult
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `business_logic/structure_validator.py` | Modify | Add `metodología`, `resultados`, and `discusión` keys to `section_map`. |

## Interfaces / Contracts

No new interfaces or contracts. The existing signature of `validate_structure` and `_extract_present_sections` remains unchanged.

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Manual | Scientific article structure validation | Run `main.py` using a sample document that contains scientific headings to confirm sections are successfully recognized and not reported missing. |

## Migration / Rollout

No migration required.
