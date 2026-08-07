# Design: JSON Report Export Adapter

## Finding — Corrects the Proposal's Premise (RESOLVED, confirmed by user 2026-08-07)

Direct source read (Step 2 of this phase) disproves two proposal claims:

1. **"No `datetime` field anywhere in `ReportInputDTO`'s tree."** False.
   `ClassificationResultDTO.timestamp`, `QualityResultDTO.timestamp`,
   `StructureValidationResultDTO.timestamp`, and `CitationAnalysisResultDTO.timestamp`
   are all real `datetime` fields. `dataclasses.asdict()` does not convert them, and
   `_prepare_for_json`'s Enum/BaseDTO-only pass does not either — a literal
   `ReportInputDTO.as_dict()` + Enum-conversion adapter (as proposed) **crashes**
   with `TypeError: Object of type datetime is not JSON serializable`.
2. **"Adapter mirrors `_prepare_for_json` for byte-for-byte parity."** False by
   omission. Today's actual JSON on disk is `_prepare_for_json(_map_report_to_legacy_dict(report))`
   — `_map_report_to_legacy_dict` (main.py:79) reshapes and curates fields first
   (renames `document_content`→`document_info`, `quality`→`quality_analysis`,
   drops all 4 `timestamp` fields, adds computed `estimated_pages`/`apa_violations`/
   `apa_compliant`, slices `unmatched_citations[:20]`, drops `verdict`/`eumic_violations`
   entirely). `ReportInputDTO.as_dict()` alone is structurally a different document.

**Resolution adopted below**: the adapter must reproduce `_map_report_to_legacy_dict`'s
exact field selection internally (as a self-contained, duplicated mapping — not by
importing from `main.py`, and without modifying `_map_report_to_legacy_dict`, which
stays in scope-excluded main.py for its other caller), then apply the Enum/BaseDTO
conversion pass. This is larger than the proposal's "plain Enum+BaseDTO pass" but is
the only way to satisfy the hard byte-for-byte-parity requirement without crashing.
**Confirmed by the user (2026-08-07) — resolved, no longer blocking.**

## Technical Approach

`JsonReportAdapter(ReportExportPort)` owns two private steps: (1) `_to_legacy_shape(report_input)` — duplicates `main.py`'s `_map_report_to_legacy_dict` field-by-field, sourced from `ReportInputDTO` instead of the dict return value; (2) `_prepare_for_json(data)` — verbatim port of `main.py`'s existing recursive Enum→`.value` / `BaseDTO`→`.as_dict()` converter. `export()` chains both, then `json.dump(..., indent=2, ensure_ascii=False)`. `ExportReportWiring.create_json_use_case()` wires a second `ExportReportUseCase` around it — zero changes to the use case. `main.py.save_json_report` calls the new use case with `self._last_report_input`; `_prepare_for_json` and the manual `json.dump` are deleted from `main.py`. `_map_report_to_legacy_dict` itself is untouched (still feeds `analyze_document()`'s CLI-print return value).

## Architecture Decisions

| Decision | Choice | Alternatives rejected | Rationale |
|---|---|---|---|
| Serialization source | Reproduce legacy-dict shape inside the adapter, then Enum/DTO-convert | (a) Raw `ReportInputDTO.as_dict()` (proposal's original plan); (b) import/call `main.py`'s `_map_report_to_legacy_dict` from the adapter | (a) crashes on datetime + breaks parity; (b) inverts hexagonal dependency direction (infra importing from the composition-root script) and risks import cycles |
| Shared mapping logic | Duplicate the field mapping in the adapter, don't extract/share | Extract a shared pure function used by both `main.py` and the adapter | Extraction touches `_map_report_to_legacy_dict`, explicitly out of scope; `main.py` is slated for removal by the paused FastAPI migration, so duplication is temporary, not a long-term liability |
| Settings injection | None — hardcoded `indent=2, ensure_ascii=False` | Injectable `JsonReportSettings` | Confirmed YAGNI in proposal; no formatting knobs requested |
| Optional-dependency guard | None | `DOCX_AVAILABLE`-style guard | `json`/`dataclasses` are always-available stdlib |

## Data Flow

    main.py: save_json_report(output_path)
        │ self._last_report_input (ReportInputDTO)
        ▼
    ExportReportUseCase.execute(report_input, output_path)
        ▼
    JsonReportAdapter.export(report_input, output_path)
        ├─ _to_legacy_shape(report_input) → dict (legacy field names/computed fields)
        ├─ _prepare_for_json(dict) → Enum→.value, BaseDTO→.as_dict() recursively
        └─ json.dump(result, f, indent=2, ensure_ascii=False)

## File Changes

| File | Action | Description |
|------|--------|--------------|
| `src/infrastructure/adapters/report/json_report_adapter.py` | Create | `JsonReportAdapter(ReportExportPort)`: `_to_legacy_shape`, `_prepare_for_json`, `export` |
| `src/infrastructure/wirings/json_report_wiring.py` | Create | **CORRECTED (2026-08-07)**: originally planned as a second `create_json_use_case()` method on `ExportReportWiring` — the user caught that this violates `.agent/skills/clean-architecture/SKILL.md` §8 ("One public method that returns the fully assembled use case"). Split into its own `JsonReportWiring` class with a single `create_use_case()`, matching every other wiring in the codebase. `export_report_wiring.py` reverted to its original single-method form. |
| `main.py` | Modify | `save_json_report` uses `self._export_json_report_use_case` (built via `JsonReportWiring().create_use_case()`); delete `_prepare_for_json`, the `dump`/`Enum`/`Any` imports it needed if now unused |
| `src/infrastructure/tests/adapters/report/fixtures.py` or new `json_fixtures.py` | Create/Modify | Real (non-`MagicMock`) `ReportInputDTO` builder — JSON serialization needs real dataclass instances, not mocks |
| `src/infrastructure/tests/adapters/report/test_json_report_adapter_*.py` | Create | init / export-success / export-failure / golden-parity, one class per file |
| `src/infrastructure/tests/test_json_report_wiring.py` | Create | Tests for `JsonReportWiring.create_use_case()` (moved out of `test_export_report_wiring.py`) |
| `src/infrastructure/tests/test_main_save_json_report.py` (or similar) | Create | First coverage of `save_json_report` call site |

## Interfaces / Contracts

No port/DTO changes. `ReportExportPort.export(report_input: ReportInputDTO, output_path: str) -> bool` unchanged.

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | `_prepare_for_json` Enum/DTO recursion | Direct calls with Enum, nested BaseDTO, list, dict inputs |
| Unit | `export()` returns `True`, writes file, propagates `IOError`→`False` (mirror Docx `export_failure` pattern) | Real temp file path, no mocks needed (stdlib `json`) |
| Golden/snapshot | Byte-for-byte parity vs. today's real output | Build one real `ReportInputDTO` fixture (all real DTOs, fixed non-random values, no `MagicMock`); commit a golden `.json` fixture generated **once** by running the pre-change `main.py` path (`_map_report_to_legacy_dict` + old `_prepare_for_json` + `json.dump`) on that exact fixture; test asserts new adapter's file bytes equal the golden file exactly |
| Wiring | `create_json_use_case()` returns `ExportReportUseCase` wired with `JsonReportAdapter` | Direct attribute assertion (`result._report_export_port`), no mocking — mirrors `test_export_report_wiring.py` |
| Integration | `save_json_report` call site | Instantiate `SilvinaEditorialAssistant`-equivalent minimal harness or test the method directly with a fake use case, assert `_last_report_input` flows through |

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary.

## Migration / Rollout

No migration. Pure code swap; `_map_report_to_legacy_dict` and `FakeReportExportPort` untouched.

## Open Questions

- [x] Adapter duplicates `_map_report_to_legacy_dict`'s field mapping — confirmed by the user 2026-08-07, no longer blocking.
- [ ] Where should the golden fixture JSON live and how is it (re-)generated if legitimate future format changes occur — propose a documented regeneration script/command in tasks.

## Key Learnings

1. `ClassificationResultDTO`, `QualityResultDTO`, `StructureValidationResultDTO`, and `CitationAnalysisResultDTO` all carry a `timestamp: datetime` field the prior exploration/proposal missed, which would crash naive JSON serialization.
2. Today's on-disk JSON is produced from `_map_report_to_legacy_dict`'s curated/renamed shape, not from `ReportInputDTO.as_dict()` directly — the two are structurally different documents (different top-level keys, computed fields, sliced arrays).
3. Existing `ReportFixtures.make_report_input_dto()` builds nested fields as `MagicMock`, which is unsuitable for a JSON golden test — a new fixture with real DTO instances is required.
4. `_map_report_to_legacy_dict` must stay duplicated (not extracted/shared) in the new adapter to respect the proposal's explicit "don't touch `_map_report_to_legacy_dict`" scope boundary and avoid infra importing from the main.py composition root.
5. CORRECTION (2026-08-07, PR 2 review): a second public method on `ExportReportWiring` (`create_json_use_case()`) violates `.agent/skills/clean-architecture/SKILL.md` §8 — every wiring in this codebase has exactly one public method returning one fully assembled use case. Fixed by giving JSON export its own `JsonReportWiring` class.
