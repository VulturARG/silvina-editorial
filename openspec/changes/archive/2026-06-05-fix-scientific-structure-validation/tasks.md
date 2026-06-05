# Tasks: Fix Scientific Structure Validation

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~15-20 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Map scientific sections and manually verify | PR 1 | Fix structure_validator.py |

## Phase 1: Implementation

- [x] 1.1 Update `section_map` in `business_logic/structure_validator.py` to add `metodología`, `resultados`, and `discusión` keys.

## Phase 2: Verification

- [x] 2.1 Create a temporary scratch script `scratch/verify_structure.py` to run `StructureValidator` on mock paragraphs.
- [x] 2.2 Verify compliant scientific article scenario (all sections present).
- [x] 2.3 Verify missing methodology scenario.
- [x] 2.4 Verify English/variant headings scenario.
