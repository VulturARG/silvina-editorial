# Feature: CLI Document Analysis

- **Feature Name**: `cli-document-analysis`
- **File Locator**: `odd/tasks/cli-document-analysis.md`
- **Branch**: `feat/cli-document-analysis` (from `silvina_editorial_v100`)
- **TDD Mode**: Enabled (RED -> GREEN -> REFACTOR) where a runnable test applies
- **TDD Runner**: `.venv/Scripts/python -m unittest discover -s src -t . -p "test_*.py"` with `USE_EXTERNAL_LLM=false APP_MODE=PROD`
- **Delivery Strategy**: stop before every commit and wait for the user's instructions; no review is launched until a task is finished

---

## 1. Objective

Rework `main.py` so that running it with a Word document analyzes it as if it had been uploaded through the web, and saves the Word, JSON and HTML reports.

## 2. Agreed specification

- Positional `document_path`: the file name. When missing, it is asked on the console.
- `--input-dir`: directory where the document is read (default: current working directory).
- `--output-dir`: directory for the reports (default: `<document directory>/análisis`). It is created when missing.
- Overrides of the `.env`, all optional: `--ollama-model-name`, `--use-external-llm true|false`, `--llm-provider`, `--external-llm-model-name`, `--app-mode DEBUG|PROD`.
- `--word-report-path` and `--json-report-path` are removed.
- Only `.docx` is accepted (same as the web). Errors are printed as plain text explaining the reason, without error codes in the message.
- Invalid Windows characters are removed from the names.
- Output files: `<document>_analisis_<model>.docx`, `.json` and `.html`, overwritten when they exist. The model is the effective one, sanitized.
- HTML: the web result as a full standalone page, CSS embedded, without download buttons.
- The console announces the start and the end of every step. At the end it prints only the end notice and the generated file paths.
- When `APP_MODE` is not DEBUG, the external LLM is silently ignored, as today.

## 3. Constraints

- Existing code is NOT modified. New behavior goes in new classes; wirings inherit from the existing ones.
- The user is asked before any change to existing code. `main.py` is the only existing file authorized to change.
- Override mechanism: `OverridableEnvConfig(EnvConfig)` sets the overrides in the process environment while the original constructor runs, then restores it. A subclass of `AnalyzeDocumentUseCaseWiring` overrides only `_get_env_config()`. `ExportReportWiring`, `JsonReportWiring` and `LoggingConfigWiring` are untouched.

## 4. Tasks

- [x] **TASK-01** `HtmlReportAdapter` (`ReportExportPort`) rendering the web result as a standalone page, plus `HtmlReportWiring`. New files only. RED first.
- [ ] **TASK-02** `OverridableEnvConfig` (subclass of `EnvConfig`) with the five overrides and environment restoration. RED first.
- [ ] **TASK-03** Wiring subclass of `AnalyzeDocumentUseCaseWiring` that uses `OverridableEnvConfig`, exposing the effective model name. RED first.
- [ ] **TASK-04** CLI support classes: report file name builder, document locator/validator with explicit messages, console step announcer, argument parser. RED first.
- [ ] **TASK-05** Rework `main.py` to the agreed flow and update the tests of the removed behavior (user approval required before touching them).

## 5. Open items

- TASK-05 will break tests of the current CLI (`tests/test_main_cli_args.py`, `tests/test_main_dto_mapping.py`, `tests/test_main_ollama_failure.py`, `tests/e2e/test_cli_e2e.py`, `src/infrastructure/tests/test_main_logging.py`, `src/infrastructure/tests/test_main_save_json_report.py`). Ask the user how to handle them before TASK-05.

## 6. Evidence

### TASK-01 (verified by the parent)

- New files only: `html_report_adapter.py`, `templates/standalone_report.html`, `html_report_wiring.py`, `test_html_report_adapter.py` (16 tests), `test_html_report_wiring.py` (3 tests).
- RED observed by the worker (`ModuleNotFoundError`), GREEN: 18 tests OK. Parent re-run: new tests 18 OK, full suite `unittest discover -s src` 1884 tests OK, `ruff check` clean.
- Known limitations: the included `_results.html` still says "Descargue el informe detallado en Word" (existing file, not changed); the embedded logo adds about 670 KB to each HTML.
- Commit: pending the user's instruction.
