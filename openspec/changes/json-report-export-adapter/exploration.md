# Exploration Report: JSON Report Export Adapter

This is a small, precisely-scoped change surfaced while designing the (now paused) `gradio-to-fastapi-migration` change: `ReportExportPort` has no JSON implementation, so both `main.py` and `gradio_app.py` hand-roll JSON serialization outside the hexagonal architecture. This report confirms the fix and its boundaries against the real code.

---

## 1. Current State

- `ReportExportPort` ([src/domain/report/report_export_port.py](file:///E:/Python/silvina-editorial/src/domain/report/report_export_port.py)) is a one-method ABC: `export(self, report_input: ReportInputDTO, output_path: str) -> bool`. Already fully format-agnostic.
- `DocxReportAdapter` ([src/infrastructure/adapters/report/docx_report_adapter.py](file:///E:/Python/silvina-editorial/src/infrastructure/adapters/report/docx_report_adapter.py)) is the only implementation today.
- `ExportReportUseCase` ([src/application/export_report_use_case.py](file:///E:/Python/silvina-editorial/src/application/export_report_use_case.py)) is already fully port-driven (`__init__(self, report_export_port: ReportExportPort)`, `execute()` just delegates) — **confirmed zero changes needed**.
- `ExportReportWiring.create_use_case()` ([src/infrastructure/wirings/export_report_wiring.py](file:///E:/Python/silvina-editorial/src/infrastructure/wirings/export_report_wiring.py)) builds exactly one Docx-backed use case instance.
- `main.py`'s `SilvinaEditorialAssistant.save_json_report` (line 166) bypasses the port entirely: manual `_prepare_for_json` (Enum → `.value`, `BaseDTO` → `.as_dict()` recursively) + `json.dump()`. `self._last_report_input: ReportInputDTO | None` is already stored after `analyze_document()` runs and is exactly what `save_word_report` already uses today.

---

## 2. Affected Areas

- `src/infrastructure/adapters/report/json_report_adapter.py` (new) — mirrors `DocxReportAdapter`'s placement/style but simpler: no optional-dependency guard needed (`json`/`dataclasses` are stdlib, unlike `python-docx`, which needs the `ReportExportUnavailable`/`DOCX_AVAILABLE` pattern — that pattern is docx-specific and should not be copied).
- `src/infrastructure/wirings/export_report_wiring.py` — add `create_json_use_case()` returning a second `ExportReportUseCase(report_export_port=JsonReportAdapter())` — a second *instance* of the existing use case class, not a new use case class.
- `main.py` — needs a second use-case instance; `save_json_report` switches to it via `self._last_report_input`. This makes `_prepare_for_json` dead code — flagged for explicit confirmation at propose time (see Risks).
- `gradio_app.py` — has its own separate `_prepare_for_json` (extra `datetime` branch, for a different DTO — `AnalysisResultDTO`, not `ReportInputDTO`). Confirmed genuinely unrelated/out of scope; not touched.

---

## 3. Confirmed Details

- `DocxReportAdapter.__init__(self, settings: DocxReportSettings, logo_path: str | None = None)` — settings-injection convention the new adapter should *not* copy (see Approaches below).
- `ReportInputDTO` (frozen dataclass extending `BaseDTO`, 11 nested DTOs) has no `datetime` field anywhere in its tree — confirms Enum+BaseDTO-only conversion is sufficient for the new adapter, unlike `gradio_app.py`'s helper.
- `BaseDTO.as_dict()` = `dataclasses.asdict()` — recurses through nested dataclasses structurally, but leaves Enum members unconverted, confirming a separate Enum pass is still required.
- Test conventions to mirror: `src/infrastructure/tests/adapters/report/` uses one test file per concern (`_init`, `_export_success`, `_export_failure`, `_field_translations`, `_settings`, shared `fixtures.py`). `src/infrastructure/tests/test_export_report_wiring.py` has 6 focused tests asserting directly on `result._report_export_port` internals, no mocks — new `create_json_use_case()` tests should follow the same style.
- `FakeReportExportPort` and `test_report_export_port.py` are format-agnostic and need no changes.
- `save_json_report` currently has **no covering test** (confirmed via codegraph blast-radius scan) — this change should add one.

---

## 4. Approaches

1. **Plain `JsonReportAdapter()`, hardcoded `indent=2, ensure_ascii=False`** — matches current `main.py` output exactly.
   - Pros: simplest, byte-for-byte parity with current output, minimal test matrix.
   - Cons: formatting knobs aren't env-configurable (unlike Docx's `DocxReportSettings`).
   - Effort: Low.

2. **Injectable `JsonReportSettings` mirroring `DocxReportSettings`** — `indent`/`ensure_ascii` from `EnvConfig`.
   - Pros: consistent with the Docx adapter's settings-injection convention.
   - Cons: over-engineering — no env vars exist or were requested for JSON formatting; violates the project's minimum-viable-solution rule (YAGNI).
   - Effort: Medium.

**Recommendation: Approach 1.**

---

## 5. Risks

- Removing `_prepare_for_json` from `main.py` as dead code touches the "no other main.py cleanup" scope boundary the user set — needs explicit confirmation before `sdd-propose` finalizes scope: remove it now (direct, unavoidable consequence of the fix) or leave it unused.
- No existing regression test for `save_json_report` to diff against — output-shape parity should be manually verified against a sample document during apply/verify.
- `gradio_app.py`'s parallel `_prepare_for_json` remains duplicated/orphaned after this change — intentionally out of scope, flagged so a future reader doesn't assume unification happened.

**Ready for proposal: yes.**
