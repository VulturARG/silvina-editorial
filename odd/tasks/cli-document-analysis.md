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

- Positional `document_name`: the file name. When missing, it is asked on the console.
- `--input-dir`: directory where the document is read (default: current working directory).
- `--output-dir`: directory for the reports (default: `<document directory>/análisis`). It is created when missing.
- Overrides of the `.env`, all optional: `--ollama-model-name`, `--use-external-llm true|false`, `--llm-provider`, `--external-llm-model-name`, `--app-mode DEBUG|PROD`.
- `--word-report-path` and `--json-report-path` are removed.
- Only `.docx` is accepted (same as the web). Errors are printed as plain text explaining the reason, without error codes in the message.
- Invalid Windows characters (`<>:"/\|?*`) are replaced with `_` in the names, as `main.py` does today.
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
- [x] **TASK-02** `OverridableEnvConfig` (subclass of `EnvConfig`) with the five overrides and environment restoration. RED first.
- [x] **TASK-03** Wiring subclass of `AnalyzeDocumentUseCaseWiring` that uses `OverridableEnvConfig`, exposing the effective model name. RED first.
- [x] **TASK-04** CLI input side in `src/infrastructure/cli/`: argument parser and its values object, document name prompter, source document locator/validator with explicit messages. RED first.
- [x] **TASK-05** CLI output side in `src/infrastructure/cli/`: file name sanitizer, report file paths builder (`<document>_analisis_<model>.<ext>`, default `análisis` directory), console step announcer. RED first.
- [x] **TASK-06** New orchestrator `DocumentAnalysisCommand` (runs the agreed steps with the step announcer and returns the exit status) plus `CliAnalysisServices`, `CliAnalysisServicesWiring` and `DocumentAnalysisCommandWiring`. New files only; it absorbs the language model error messages tested today by `tests/test_main_ollama_failure.py`. RED first.
- [x] **TASK-07** Rework `main.py` to the new flow: delete `SilvinaEditorialAssistant` and the old argument parser (user decision B), delete the 4 test modules of that class, rewrite the tests of `main()`, add an end-to-end test of the whole flow with the mocked Ollama client, and update the README usage.

## 5. Open items

- TASK-07 will break tests of the current CLI (`tests/test_main_cli_args.py`, `tests/test_main_dto_mapping.py`, `tests/test_main_ollama_failure.py`, `tests/e2e/test_cli_e2e.py`, `src/infrastructure/tests/test_main_logging.py`, `src/infrastructure/tests/test_main_save_json_report.py`). Decision of the user (option B): `SilvinaEditorialAssistant` is deleted together with `tests/test_main_dto_mapping.py`, `tests/test_main_ollama_failure.py`, `tests/e2e/test_cli_e2e.py` and `src/infrastructure/tests/test_main_save_json_report.py`; `tests/test_main_cli_args.py` and `src/infrastructure/tests/test_main_logging.py` are rewritten for the new `main()`. Stale mentions to decide later: the docstring of `JsonReportAdapter._to_legacy_shape` and `docs/plan-migracion-hexagonal.md` name the deleted `_map_report_to_legacy_dict`.

## 6. Evidence

### TASK-01 (verified by the parent)

- New files only: `html_report_adapter.py`, `templates/standalone_report.html`, `html_report_wiring.py`, `test_html_report_adapter.py` (16 tests), `test_html_report_wiring.py` (3 tests).
- RED observed by the worker (`ModuleNotFoundError`), GREEN: 18 tests OK. Parent re-run: new tests 18 OK, full suite `unittest discover -s src` 1884 tests OK, `ruff check` clean.
- Known limitations: the included `_results.html` still says "Descargue el informe detallado en Word" (existing file, not changed); the embedded logo adds about 670 KB to each HTML.
- Commit: `fa8fc79` feat(report): export the analysis as a standalone HTML page.

### TASK-02 (verified by the parent)

- New files: `src/infrastructure/overridable_env_config.py`, `src/infrastructure/tests/test_overridable_env_config.py` (11 tests).
- RED observed by the worker (`ModuleNotFoundError`), GREEN: 11 tests OK. Mutation check by the parent: removing the environment restoration makes 3 tests fail; restored afterwards.
- Extra step approved by the user (replaces a brittle `parents[n]` computation, and removes the private import): new package `src/infrastructure/resources/project/__init__.py` exposing public `PROJECT_ROOT_DIR`, `SETTINGS_FILE_PATH`, `VERSION_FILE_PATH` and `EDITORIAL_NORMS_FILE_PATH`, in the style of the other resource packages. Existing files modified with the user's approval: `env_config.py` (private constants removed, public ones imported), `analyze_document_use_case_wiring.py` (`_EDITORIAL_NORMS_PATH` removed), and one patch target in `test_env_config.py`. New test: `test_project_resources.py` (8 tests, RED observed as `ModuleNotFoundError`).
- Parent verification: full suite 1903 tests OK, ruff check and format clean on the changed production files, LSP diagnostics clean on the modified files.
- Commits: `3d1d0ce` refactor(config): centralize project file paths in a resources package; `a91591e` feat(config): add OverridableEnvConfig with temporary environment overrides.

### TASK-03 (verified by the parent)

- New files only: `src/infrastructure/wirings/overridable_analyze_document_use_case_wiring.py` (overrides only `_get_env_config()`, exposes `get_active_model_name()` delegating to the parent), `src/infrastructure/tests/test_overridable_analyze_document_use_case_wiring.py` (11 tests).
- RED observed by the worker (`ModuleNotFoundError`), GREEN: 11 tests OK. Parent re-run: full suite 1914 tests OK, ruff clean, pyright CLI 0 errors (the LSP import warning is a stale index).
- Findings for TASK-06: `ExportReportWiring` (`EnvConfig()` at `export_report_wiring.py:180`) and `WarmUpLanguageModelUseCaseWiring` (`warm_up_language_model_use_case_wiring.py:40`) build their own `EnvConfig()`, so they ignore the overrides. The Word report does not use any of the five overridden values. The CLI must not call the warm-up use case, or it would warm up the model from the `.env`.
- Commit: `0978b02` feat(config): add OverridableAnalyzeDocumentUseCaseWiring.

### TASK-04 (verified by the parent)

- New files: `src/infrastructure/cli/` (`__init__.py`, `command_line_arguments.py`, `command_line_argument_parser.py`, `document_name_prompter.py`, `source_document_locator.py`) and four flat test modules in `src/infrastructure/tests/` (36 tests).
- RED observed by the worker (`ModuleNotFoundError: No module named 'src.infrastructure.cli'`), GREEN: 36 tests OK. Parent re-run: full suite 1950 tests OK, ruff clean, pyright CLI 0 errors.
- Extra step approved by the user: `DocumentNotFound` and `DocumentInvalidType` (`src/domain/exceptions/document_errors.py`, existing file) gain an optional `detail`, following the `SettingsFileNotFound` pattern. Without a detail `dict()` is identical to before, so the web and the other callers are unaffected. 10 tests added to `test_document_not_found.py` and `test_document_invalid_type.py` (none altered); the locator raises with `detail=<resolved path>`. Parent verification: full suite 1960 tests OK, ruff clean, pyright 0 errors on production files.
- Known and pre-existing: pyright reports `len(MESSAGE)` in the existing `test_message_is_not_empty` of those two test modules (also reported on `HEAD`); not touched.
- Commits: pending the user's instruction (two: the domain `detail` change first, then the CLI input side).

### TASK-05 (verified by the parent)

- New files: `src/infrastructure/cli/` (`windows_file_name_sanitizer.py`, `report_file_paths.py`, `report_file_paths_builder.py`, `console_step_announcer.py`) and three flat test modules in `src/infrastructure/tests/` (21 tests). No existing file modified.
- RED observed by the worker (`ModuleNotFoundError`), GREEN: 21 tests OK. Parent re-run: full suite 1981 tests OK, ruff clean, pyright CLI 0 errors.
- Spec wording fixed: invalid characters are replaced with `_` (the user had accepted this), not removed.
- Commit: `206abac` feat(cli): add file name sanitizer, report file paths builder and console step announcer.

### TASK-06 (verified by the parent)

- New files: `src/infrastructure/cli/` (`cli_analysis_services.py`, `document_analysis_command.py`), `src/infrastructure/wirings/` (`cli_analysis_services_wiring.py`, `document_analysis_command_wiring.py`) and three flat test modules in `src/infrastructure/tests/` (29 tests). No existing file modified.
- RED observed by the worker (`ModuleNotFoundError`), GREEN: 27 tests OK.
- Two defects found by the parent from the worker's report and fixed test-first (RED: 2 failures, then GREEN): a failed Word export no longer prints `terminado` for its step; a blank answer to the document name prompt ends with `No se indicó el nombre del documento` (status 2) instead of reporting the current directory as a missing document.
- Parent verification: full suite 2010 tests OK, ruff clean, pyright CLI 0 errors.
- Known and not covered: `JSON`/`HTML` use cases returning `False` are not treated as failures (only Word can return `False` today, and the spec only defines the Word failure); the web's maximum upload size is not enforced by the CLI.
- Commit: `60a9a5a` feat(cli): add the document analysis command and its wirings.

### TASK-07 (verified by the parent)

- `main.py` rewritten (configure logging, banner, `CommandLineArgumentParser`, `DocumentAnalysisCommandWiring().create_command().run(...)`, `exit` only on a non-zero status). `SilvinaEditorialAssistant` and the old argument parser deleted (user decision B).
- Deleted: `tests/test_main_dto_mapping.py`, `tests/test_main_ollama_failure.py`, `src/infrastructure/tests/test_main_save_json_report.py`. Rewritten: `tests/test_main_cli_args.py` (5), `src/infrastructure/tests/test_main_logging.py` (2), `tests/e2e/test_cli_e2e.py` (5, in-process with the mocked Ollama client). README: new Command Line subsection.
- Parent verification: `unittest discover -s src` 2008 tests OK (2010 before: 2 fewer after deleting a module), `pytest tests` 35 passed (51 before: 16 tests of deleted or rewritten modules), ruff and pyright clean.
- Real run by the parent against the fixture (external model from the `.env`): all steps announced with start and end, exit status 0 after about 115 s, files `capacidades_razonamiento_emergente_LLMs_analisis_claude-haiku-5-5.docx|.json|.html` created in `análisis/` next to the document; the JSON is valid (3613 words), the HTML is a standalone page of about 702 KB with embedded CSS and no script, no external URL and no download link. A previous run failed with the clean message "The language model backend is unavailable." (provider unreachable at that moment); the error path prints the domain message and ends with a non-zero status.
- Stale mentions left untouched on purpose: the docstring of `JsonReportAdapter._to_legacy_shape`, `docs/plan-migracion-hexagonal.md` and the comments of `scripts/regenerate_json_export_golden_fixture.py` still name the deleted `_map_report_to_legacy_dict`.
- Commit: pending the user's instruction.
