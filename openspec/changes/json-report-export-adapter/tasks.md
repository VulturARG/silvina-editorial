# Tasks: JSON Report Export Adapter

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~480–560 (adapter ~130, tests ~150, real-DTO fixture ~90, regen script ~40, wiring +6/+tests ~15, main.py diff ~35, main.py test ~50; golden `.json` bytes excluded per guard) |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1: adapter + golden fixture + regen script + tests → PR 2: wiring + main.py integration |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: pending
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|------------------|--------------------|
| 1 | `JsonReportAdapter` fully tested standalone, golden-parity proven | PR 1 | `.venv\Scripts\python -m pytest src/infrastructure/tests/adapters/report -q` | `.venv\Scripts\python scripts\regenerate_json_export_golden_fixture.py` (real script run) | Delete `json_report_adapter.py`, its tests, `json_fixtures.py`, golden fixture, regen script — no other file touched |
| 2 | Wiring + `main.py` call-site swap | PR 2 | `.venv\Scripts\python -m pytest src/infrastructure/tests/test_export_report_wiring.py src/infrastructure/tests/test_main_save_json_report.py -q` | N/A — no automated CLI harness in this project; manual `python main.py <doc>.docx` smoke available but not required | Revert `export_report_wiring.py` and `main.py` diffs; PR 1 artifacts remain valid and untouched |

## Phase 0: Golden Fixture (decision, not open question)

- [x] 0.1 Create `src/infrastructure/tests/adapters/report/json_fixtures.py` — `JsonReportFixtures.make_real_report_input_dto()`: real (non-`MagicMock`) nested DTOs incl. `datetime` timestamps, fixed non-random values, Enum members for `article_type`, `recommendations[].priority`, `apa_validation.violations[].error_type`.
- [x] 0.2 Create `scripts/regenerate_json_export_golden_fixture.py`: self-contained frozen copy of pre-change `_map_report_to_legacy_dict` + old `_prepare_for_json` (not imported from `main.py`, since that code is deleted in Phase 5), run against `JsonReportFixtures`, writes `src/infrastructure/tests/adapters/report/fixtures/json_export_golden.json`. Docstring documents: regenerate only after an intentional, reviewed adapter format change.
- [x] 0.3 Run the script once; commit the golden `.json` (excluded from authored line budget, included in snapshot identity).

## Phase 1: `_prepare_for_json` (RED → GREEN)

- [x] 1.1 [RED] `test_json_report_adapter_prepare_for_json.py`: Enum→`.value`, nested `BaseDTO`→`.as_dict()`, list/dict recursion, passthrough scalars.
- [x] 1.2 [GREEN] Create `src/infrastructure/adapters/report/json_report_adapter.py` — `JsonReportAdapter(ReportExportPort)` with `_prepare_for_json` ported verbatim from `main.py`.

## Phase 2: `_to_legacy_shape` + `export()` (RED → GREEN)

- [x] 2.1 [RED] `test_json_report_adapter_init.py`: `JsonReportAdapter()` takes no args.
- [x] 2.2 [RED] `test_json_report_adapter_export_success.py`: `export()` returns `True`, file exists, legacy-shape keys present (`document_info`, `quality_analysis`, `citations_analysis`, etc.), Enum fields serialized as strings.
- [x] 2.3 [RED] `test_json_report_adapter_export_failure.py`: unwritable path → `OSError` propagates.
- [x] 2.4 [GREEN] Implement `_to_legacy_shape` (duplicate `_map_report_to_legacy_dict` field-by-field) and `export()` chaining `_to_legacy_shape` → `_prepare_for_json` → `json.dump(indent=2, ensure_ascii=False)`.

## Phase 3: Golden Parity (RED → GREEN)

- [x] 3.1 [RED] `test_json_report_adapter_golden_parity.py`: `export()` output bytes == committed golden file bytes, using `JsonReportFixtures`.
- [x] 3.2 [GREEN] Fix any `_to_legacy_shape` mapping drift until byte-identical. No drift found — implementation matched the golden fixture on first execution.

## Phase 4: Wiring (RED → GREEN)

**CORRECTED (2026-08-07)**: the plan below (a second method on `ExportReportWiring`) was rejected in code review for violating `.agent/skills/clean-architecture/SKILL.md` §8. Implemented instead as a standalone `JsonReportWiring` class in `src/infrastructure/wirings/json_report_wiring.py`, tested in its own `test_json_report_wiring.py` — `export_report_wiring.py`/`test_export_report_wiring.py` stayed untouched (zero diff vs. pre-change base).

- [x] 4.1 [RED] Create `test_json_report_wiring.py`: `JsonReportWiring().create_use_case()` returns `ExportReportUseCase` (exact class) whose `_report_export_port` is `JsonReportAdapter`.
- [x] 4.2 [GREEN] Create `JsonReportWiring` with a single `create_use_case()` in `json_report_wiring.py`.

## Phase 5: `main.py` Integration (Approval Testing, RED → GREEN)

- [x] 5.1 Safety net: run existing tests touching `main.py` — baseline.
- [x] 5.2 [RED] `test_main_save_json_report.py`: `save_json_report` invokes JSON-wired `ExportReportUseCase.execute(report_input=self._last_report_input, output_path=output_path)`; `_prepare_for_json` attribute no longer exists on `SilvinaEditorialAssistant`.
- [x] 5.3 [GREEN] Wire `self._export_json_report_use_case` in `__init__`; rewrite `save_json_report`; delete `_prepare_for_json` and now-unused `dump`/`Enum`/`Any` imports if unused elsewhere in `main.py`.

## Phase 6: Verification

- [x] 6.1 Run `.venv\Scripts\python -m pytest src/ -q` — full scoped suite green, no regressions.
- [x] 6.2 Confirm `gradio_app.py`'s own `_prepare_for_json`/`json.dump` path is untouched (explicitly out of scope).
- [x] 6.3 Confirm no `src/domain/` import from `src/application/` or `src/infrastructure/`.

## Key Learnings

1. `main.py`'s current `save_json_report`/`_prepare_for_json` (lines 166–188) and `_map_report_to_legacy_dict` (line 79) are the exact source the adapter must duplicate — read via codegraph before drafting tasks.
2. `gradio_app.py` has its own independent `_prepare_for_json` (with `datetime.isoformat()` handling) that is explicitly out of scope and must stay untouched.
3. The existing `ReportFixtures.make_report_input_dto()` builds `MagicMock` nested fields, unusable for JSON golden tests — a new real-DTO fixture (`JsonReportFixtures`) is required.
4. The golden fixture must be generated from a frozen, standalone copy of the pre-change logic (not by importing `main.py`), since `_prepare_for_json` is deleted from `main.py` in Phase 5 of this same change.
