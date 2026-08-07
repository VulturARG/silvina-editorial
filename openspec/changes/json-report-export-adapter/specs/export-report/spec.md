# Delta for export-report

## ADDED Requirements

### Requirement: JsonReportAdapter Implements ReportExportPort

`JsonReportAdapter(ReportExportPort)` MUST reside in `src/infrastructure/adapters/report/json_report_adapter.py`, require no settings or configuration object, and serialize the given `ReportInputDTO` by (1) reproducing `main.py`'s `_map_report_to_legacy_dict` field mapping internally (duplicated logic, not imported from `main.py`) to obtain the legacy dict shape, then (2) applying a recursive Enum→`.value` / `BaseDTO`→`.as_dict()` conversion pass equivalent to `main.py`'s current `_prepare_for_json`, before writing with `json.dump(indent=2, ensure_ascii=False)`. A plain `ReportInputDTO.as_dict()` dump is explicitly insufficient: `ReportInputDTO`'s tree contains real `datetime` fields that crash naive serialization, and its structure differs from the legacy dict (renamed keys, computed fields, dropped/sliced fields) that is actually on disk today. Output structure MUST match today's real `main.py` `_map_report_to_legacy_dict()` + `_prepare_for_json()` + `json.dump()` pipeline exactly — this is a compatibility contract because the file is read by systems external to this application, not just an internal preference.

#### Scenario: Successful export returns True

- GIVEN a valid `ReportInputDTO` and a writable `path`
- WHEN `JsonReportAdapter.export(report_input, path)` is called
- THEN it returns `True` and a `.json` file exists at `path`

#### Scenario: Output is byte-for-byte identical to today's real production pipeline

- GIVEN a real sample `ReportInputDTO` fixture
- WHEN `JsonReportAdapter.export(report_input, path)` writes `path`, and separately today's real pre-change pipeline — `_map_report_to_legacy_dict(report_input)` then `_prepare_for_json(...)` then `json.dump(..., indent=2, ensure_ascii=False)` — writes `golden_path` from the same fixture
- THEN the raw bytes of `path` and `golden_path` are identical

#### Scenario: Nested Enum fields are converted to their .value

- GIVEN a `ReportInputDTO` fixture whose `verdict`, `recommendations[].priority`, and `apa_validation.violations[].error_type` are Enum members
- WHEN `JsonReportAdapter.export(report_input, path)` is called
- THEN the written JSON contains the Enum's `.value` (a string) at every one of those fields, never a Python Enum repr

#### Scenario: IO error propagates to caller

- GIVEN a path that cannot be written
- WHEN `JsonReportAdapter.export(report_input, path)` is called
- THEN the underlying `OSError` propagates; `@generic_error_handler` on the use case wraps it as `SrcGenericError`

---

### Requirement: ExportReportWiring JSON Factory

`ExportReportWiring.create_json_use_case()` MUST instantiate `JsonReportAdapter()` with no settings and return an `ExportReportUseCase` wired with it. It MUST reuse the existing `ExportReportUseCase` class unchanged — no new use-case class is introduced for JSON.

#### Scenario: Wiring returns a fully wired JSON use case

- GIVEN `ExportReportWiring()`
- WHEN `create_json_use_case()` is called
- THEN it returns an `ExportReportUseCase` instance whose port is a `JsonReportAdapter`
- AND the returned object's class is exactly `ExportReportUseCase`, the same class `create_use_case()` returns

---

### Requirement: main.py save_json_report Uses the Hexagonal JSON Use Case

`SilvinaEditorialAssistant.save_json_report` MUST call the JSON-wired `ExportReportUseCase` with `self._last_report_input`, replacing the previous manual `json.dump()` call. `main.py` MUST NOT define `_prepare_for_json` after this change.

#### Scenario: save_json_report delegates to the JSON use case

- GIVEN an initialized `SilvinaEditorialAssistant` with `self._last_report_input` set after `analyze_document()`
- WHEN `save_json_report(analysis_results, output_path)` is called
- THEN the JSON-wired `ExportReportUseCase.execute` is invoked with `report_input=self._last_report_input` and `path=output_path`

#### Scenario: _prepare_for_json no longer exists

- GIVEN the updated `main.py` source
- WHEN `SilvinaEditorialAssistant` is inspected for a `_prepare_for_json` attribute
- THEN no such method is defined
