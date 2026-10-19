# Feature: Batch Runner (`batch-main.py`)

- **Feature Name**: `batch-main`
- **File Locator**: `odd/tasks/batch-main.md`
- **Branch**: `feat/batch-main` (created from `silvina_editorial_v200`)
- **TDD Mode**: Test-first (RED then GREEN) for every task with runnable deterministic tests
- **TDD Runner**: `export APP_MODE=PROD; .venv/Scripts/python.exe -m unittest discover -s src -t . -p "test_*.py"` and the same with `-s tests`
- **Commit policy**: one work-unit commit per task (Conventional Commits); push, PR and merge stay the user's decisions

---

## 1. Objective

A developer-only script, `batch-main.py`, at the repository root. It reads a batch TOML file (path given as argument) and runs the same analysis `main.py` runs, looping over runs (models/parameters) first and over documents second. Any failure, including Ctrl+C, stops the whole batch.

## 2. Evidence

- `main.py` parses arguments and calls `DocumentAnalysisCommandWiring().create_command().run(arguments)`; `DocumentAnalysisCommand.__init__` only stores collaborators and `run` builds the services on every call, so one command can be reused across iterations.
- `CommandLineArguments` (frozen dataclass) carries every variable parameter: `ollama_model_name`, `use_external_llm`, `llm_provider`, `external_llm_model_name`, `app_mode`, the prompt overrides and `prompts_directory`, plus `document_name`, `input_directory`, `output_directory`.
- Report names encode only the model and the prompt source (`ReportFilePathsBuilder`), so runs that differ only in provider or app mode would overwrite each other unless each run has its own output directory.
- Silent failures in `DocumentAnalysisCommand` (`src/infrastructure/cli/document_analysis_command.py`): `KeyboardInterrupt` returns `SUCCESS_STATUS` (lines 53-55); JSON and HTML export results are ignored (lines 140-151); `_release_language_model_server` swallows every exception (`except Exception: pass`).
- Existing tests that pin the current behaviour and must change: `test_keyboard_interrupt_returns_zero_with_interruption_message`, `test_failing_release_does_not_alter_exit_status_on_success`, `test_failing_release_does_not_hide_original_error` in `src/infrastructure/tests/test_document_analysis_command.py`.
- The project reads TOML with the stdlib `tomllib` (`settings_file_loader.py`, `editorial_norms_toml_reader.py`); Python 3.12.

## 3. Design

- Batch file is independent of `analysis_settings.toml` and `editorial_norms.toml`; it has its own reader. Several batch files may exist per package; relative paths resolve against the batch file location.
- Schema: `[batch]` holds `input_directory`, `output_directory` and `documents` (omitted or `"all"` = every `.docx` of `input_dir` in name order; a list = those file names). Each `[[run]]` has a `name` and any `CommandLineArguments` field except the document name (all 15 fields are covered; `input_directory` and `output_directory` may also be overridden per run); a run may override `documents`, otherwise it uses the batch ones, so the same documents are processed with every model. Report file names are the existing ones (document, model and prompt source); the output directory is not split per run. Two runs that differ only in a field absent from the file name overwrite each other unless they use different `output_dir` values.
- No custom validation: unknown keys fail at `CommandLineArguments(**fields)`, everything else fails when the command runs. The batch stops at the first non-zero status.
- A missing document name never reaches the command: the runner always supplies one.
- Everything lives in `src/infrastructure/cli/` (driving side) with a wiring in `src/infrastructure/wirings/`; `batch-main.py` stays as thin as `main.py`.

## 4. Tasks

- [x] **TASK-01: Ctrl+C is a failure, not a success**
  - **Scope**: `document_analysis_command.py`, `test_document_analysis_command.py`, `tests/e2e/test_cli_e2e.py` if affected. New `INTERRUPTED_STATUS`; `main.py` already exits on any non-zero status.
  - **Outcome**: `run` returns `INTERRUPTED_STATUS = 130` on `KeyboardInterrupt` (RED: missing constant; GREEN; `src` 2324 and `tests` 34 OK; ruff clean). Commit `fc9e150`.
- [x] **TASK-02: JSON and HTML export failures fail the run**
  - **Scope**: same command and its tests; announce an error per report and return `FAILURE_STATUS`.
  - **Outcome**: JSON and HTML export results are checked like the Word one; a failed export announces its own message and returns `FAILURE_STATUS` (RED 4 failures, GREEN; `src` 2330 and `tests` 34 OK; ruff clean). Commit `88c0613`.
- [x] **TASK-03: A failing server release is reported, not swallowed**
  - **Scope**: same command and its tests; the release error is logged and announced, turns an otherwise successful run into `FAILURE_STATUS` and never hides an earlier error.
  - **Outcome**: the release error is logged and announced; an otherwise successful run returns `FAILURE_STATUS`, other statuses are kept (RED 3 failures, GREEN; `src` 2331 and `tests` 34 OK; ruff clean). Commit `d09f877`.
- [x] **TASK-04: Batch file model and reader**
  - **Scope**: new frozen dataclasses for the plan and its runs, a TOML reader that builds `CommandLineArguments`, a document selector (all or named), with `unittest` tests.
  - **Outcome**: `BatchRun`, `BatchPlan`, `BatchDocumentSelector` and `BatchFileReader` in `src/infrastructure/cli/`; field names of the TOML are the `CommandLineArguments` field names; `use_external_llm` defaults to false, an external run without `app_mode = "DEBUG"` is rejected, `~$` lock files are skipped, an empty or `all`-without-matches document selection raises (RED import errors, GREEN 34 tests; `src` 2365 and `tests` 34 OK; ruff and LSP clean). Commit `0fa7f51`.
- [x] **TASK-05: Batch runner**
  - **Scope**: loop runs then documents, reuse one command, stop at the first non-zero status, announce which run and document failed; tests with a fake command.
  - **Outcome**: `BatchRunner(analysis_command, console_step_announcer).run(plan)` loops runs then documents, announces start/finish, stops at the first non-zero status returning it unchanged and lets exceptions and `KeyboardInterrupt` propagate (RED import error, GREEN 12 tests; `src` 2377 and `tests` 34 OK; ruff clean). Commit `2d3f0d4`.
- [x] **TASK-06: Wiring, `batch-main.py` and docs**
  - **Scope**: `BatchCommandLineArgumentParser` (one positional batch file path), `BatchCommand` (reads the plan, reports file errors with status 1, maps `KeyboardInterrupt` to `INTERRUPTED_STATUS`, runs the runner), `BatchCommandWiring`, root `batch-main.py` as thin as `main.py`, two sample batch files in `sandbox/pack_2/` (documents 01 and 02, and all documents), README section, tests.
  - **Outcome**: `BatchCommandLineArgumentParser`, `BatchCommand`, `BatchCommandWiring`, root `batch-main.py`, `sandbox/pack_2/batch_two_documents.toml` and `batch_all_documents.toml`, README "Batch runs" section (RED 9 errors, GREEN 62 tests; `src` 2393 and `tests` 34 OK; ruff clean; smoke: no argument exits 2, missing file exits 1). Commit `6ae4023`.
- [x] **TASK-07: Verification**
  - **Scope**: full `src` and `tests` suites, ruff, and a dry run of the sample batch (delegated to `gentle-ai-verify`).
  - **Outcome**: verifier PASS with no blocker or major finding (`src` 2393 and `tests` 34 OK, ruff clean, no silent failure path found, both samples read with the real reader, `batch-main.py` exits 2 without arguments and 1 with a missing file). Not verified: a real analysis with Ollama or Claude and a live Ctrl+C. Minor findings handled: pyright errors in tests fixed and the redundant batch tests trimmed (batch tests 62 to 38, suites now `src` 2365 and `tests` 34), commit `31048f5`; schema names and the `app_mode` decision corrected in this document. Open minor items: a failed export does not show its cause; the reader catches only `OSError`, `ValueError` and `TypeError`.

## 5. Open decisions (defaults proposed, pending user confirmation)

- DECIDED by the user: report file names and output directory stay as they are (no subfolder per run).
- DECIDED by the user: a release failure fails the run.
- DECIDED by the user: Word lock files (`~$*.docx`, hidden temporary files Word creates next to an open document) are skipped when selecting all documents.
- DECIDED (implemented): `use_external_llm` defaults to `false` so no run inherits it from `.env`; no `app_mode` default is forced (it also drives the audit payload policy); the reader stops the batch before starting when a run has `use_external_llm = true` without `app_mode = "DEBUG"`, because `EnvConfig` would silently fall back to Ollama (`_parse_llm_provider`, `env_config.py:292`).
- NOTE: Ollama and external (Claude) runs can be mixed: provider-dependent steps (server check, warm-up, release) are resolved per run from its own services. External runs need `requirements-debug.txt` (`claude-agent-sdk`). Group consecutive Ollama runs to avoid an idle shutdown of the local server during an external run.
- DECIDED by the user's silence, explained: no `[[sweep]]`/Cartesian expansion in the first version; runs are explicit.
