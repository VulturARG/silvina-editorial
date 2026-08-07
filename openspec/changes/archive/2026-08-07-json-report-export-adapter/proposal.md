# Proposal: JSON Report Export Adapter

## Intent

`ReportExportPort` has a `.docx` implementation but no JSON one, so `main.py`'s `save_json_report` bypasses the hexagonal architecture entirely: manual `json.dump()` plus a hand-rolled `_prepare_for_json` (Enum → `.value`, `BaseDTO` → `.as_dict()`) live outside any adapter/use-case boundary, and the path has zero test coverage. This closes that architecture gap the same way Docx export already works, without touching anything else in `main.py`.

## Scope

### In Scope
- New `JsonReportAdapter(ReportExportPort)` at `src/infrastructure/adapters/report/json_report_adapter.py` — no settings injection, hardcoded `indent=2, ensure_ascii=False`. **CORRECTED (2026-08-07)**: a plain `ReportInputDTO.as_dict()` + Enum-conversion pass was disproven during design — `ReportInputDTO`'s tree has real `datetime` fields (crashes naive serialization) and today's actual on-disk JSON comes from `_map_report_to_legacy_dict`'s renamed/curated shape, not a raw DTO dump. The adapter must internally reproduce `_map_report_to_legacy_dict`'s exact field mapping (duplicated, not imported from `main.py`), then apply the Enum/`BaseDTO` conversion pass, to satisfy true byte-for-byte parity. Confirmed by the user — see design.md's former "BLOCKING Finding".
- `ExportReportWiring.create_json_use_case()` — a second factory returning a second `ExportReportUseCase` instance wired with `JsonReportAdapter()`. `ExportReportUseCase` itself is unchanged.
- `main.py`'s `save_json_report` switches to this new use-case instance, calling it with `self._last_report_input` (already stored after `analyze_document()`), replacing the manual `json.dump()`/`_prepare_for_json` call.
- Remove `_prepare_for_json` from `main.py` — it becomes dead code as a direct, unavoidable consequence of this fix.
- Test coverage: new adapter (mirroring `DocxReportAdapter`'s test split), new wiring factory (mirroring `test_export_report_wiring.py`'s no-mock style), and a first test for `save_json_report` (currently untested).

### Out of Scope
- Any other `main.py` cleanup (composition-root duplication, `_map_report_to_legacy_dict`, CLI print formatting) — low ROI since `main.py` is slated for FastAPI replacement in the separate, currently-paused `gradio-to-fastapi-migration` change.
- `gradio_app.py` and its own unrelated `_prepare_for_json` (different DTO — `AnalysisResultDTO`).
- `ExportReportUseCase` — already correct, confirmed in exploration.
- Anything depending on or referencing `gradio-to-fastapi-migration`.
- Injectable `JsonReportSettings` (mirroring `DocxReportSettings`) — YAGNI, no formatting knobs requested.

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `export-report`: adds a JSON-format `ReportExportPort` implementation (`JsonReportAdapter`) and a second wiring factory (`create_json_use_case()`); no changes to existing Docx requirements.

## Approach

Mirror the existing Docx adapter's placement and hexagonal wiring exactly — JSON is stdlib, so no optional-dependency guard (`ReportExportUnavailable`/`DOCX_AVAILABLE`) is needed. `ExportReportWiring` gains a sibling factory method rather than a new use-case class, since `ExportReportUseCase` is already fully port-driven. `main.py` is touched only at the call site of `save_json_report`, keeping the rest of its (soon-to-be-replaced) composition logic untouched. The adapter itself is larger than originally estimated (see corrected In Scope bullet above): it duplicates `_map_report_to_legacy_dict`'s field selection internally before applying the Enum/`BaseDTO` conversion pass, since that is the only way to match today's real on-disk output exactly.

## Affected Areas

| Area | Impact | Description |
|------|--------|--------------|
| `src/infrastructure/adapters/report/json_report_adapter.py` | New | `JsonReportAdapter(ReportExportPort)` |
| `src/infrastructure/wirings/export_report_wiring.py` | Modified | Add `create_json_use_case()` |
| `main.py` | Modified | `save_json_report` uses new use case; `_prepare_for_json` removed |
| `src/infrastructure/tests/adapters/report/` | New | Adapter tests (init/export-success/export-failure/field-translations) |
| `src/infrastructure/tests/test_export_report_wiring.py` | Modified | Tests for `create_json_use_case()` |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Output-shape parity regression vs. current `json.dump()` output | Low, but high-impact if it happens | **Hard requirement, not just internal consistency**: the user confirmed this JSON file is read by consumers external to this app, so the output must be structurally identical before and after this change. Adapter mirrors `_prepare_for_json` logic exactly; test must include a golden-file/snapshot comparison against real `json.dump()`+`_prepare_for_json` output on a sample `ReportInputDTO`, not just field-level assertions |
| `_prepare_for_json` removal seen as scope creep | Low | Confirmed by user as a direct, unavoidable consequence — not a separate cleanup |

## Rollback Plan

Revert the commit. `ExportReportUseCase` and `FakeReportExportPort` are unchanged, so no data/schema migration in either direction; `save_json_report` reverting to `json.dump()` is a pure code revert.

## Dependencies

None — reuses `ReportExportPort`, `ExportReportUseCase`, and `ReportInputDTO` unchanged.

## Success Criteria

- [ ] `JsonReportAdapter.export()` produces output byte-identical in structure to the current `main.py` `_prepare_for_json` + `json.dump()` path — **external consumers read this file, so this is a compatibility contract, not just an internal preference**.
- [ ] A golden-file/snapshot test proves the above on a real sample `ReportInputDTO`, not only field-level unit assertions.
- [ ] `save_json_report` has test coverage (previously zero).
- [ ] `_prepare_for_json` no longer exists in `main.py`.
- [ ] `ExportReportUseCase` and `FakeReportExportPort` remain unmodified.

## Key Learnings

1. `export-report` is an existing OpenSpec capability with a full spec; this change is a Modified Capability delta (new adapter/wiring requirements), not a new capability.
2. The new adapter needs no `DOCX_AVAILABLE`-style guard because `json`/`dataclasses` are stdlib, unlike `python-docx`.
3. `_last_report_input` is already stored on `SilvinaEditorialAssistant` after `analyze_document()`, so no new state plumbing is needed in `main.py`.
