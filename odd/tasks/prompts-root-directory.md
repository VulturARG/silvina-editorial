# Feature: Prompts Root Directory (CLI)

- **Feature Name**: `prompts-root-directory`
- **File Locator**: `odd/tasks/prompts-root-directory.md`
- **Branch**: `feat/prompts-root-directory` (from `silvina_editorial_v200`)
- **TDD Mode**: Enabled (RED -> GREEN -> REFACTOR) where a runnable test applies
- **TDD Runner**: `.venv/Scripts/python -m unittest discover -s src -t . -p "test_*.py"` with `USE_EXTERNAL_LLM=false APP_MODE=PROD`
- **Delivery Strategy**: one work-unit commit per task on the feature branch; push, pull request and merge stay with the user

---

## 1. Objective

Let `main.py` receive one optional argument that replaces the whole default prompts root (`src/infrastructure/resources/prompts`), so a complete prompt set can be tested at once. Report which prompt source a CLI run used, in the log and in the reports; never in the web flow.

## 2. Agreed specification

- New optional flag `--prompts-dir <directory>`. The directory must have the same layout and file names as the default root: `classification/s4_s5_s6_signal_prompt.txt` and `quality/{alignment_prompt,argumentation_conclusions_prompt,clarity_coherence_prompt,contribution_prompt,research_lines}.txt`.
- Validation is STRICT and happens in the argument parser, before anything runs: the directory must exist and contain all six files. A missing file is a usage error. There is never a silent fallback to the packaged prompt.
- The six existing per-prompt flags keep working and take precedence over the root: per-prompt flag, then custom root, then packaged default. The strict root validation applies even when a per-prompt flag covers one of the files.
- Relative paths resolve against the directory the CLI is run from, like the existing flags. Extra files in the root are ignored.
- The `v2` prompt set under `resources/prompts/v2/` is renamed so its files drop the `_v2` suffix, to satisfy the same-names rule.
- The reported prompt source is ONE value per run with two parts:
  1. Base: `default` when `--prompts-dir` is absent, otherwise the name of the root folder (for example `v2`).
  2. Replaced prompts: the names of the prompts replaced by per-prompt flags, in the fixed order of `CommandLineArguments.PROMPT_NAMES`; omitted when there are none.
  - Examples: `default`; `v2`; `default + clarity_coherence_prompt, research_lines`; `v2 + alignment_prompt`.
- It is shown in the CLI log and in the Word, JSON and HTML reports. The web flow does not show it and its output does not change.

## 3. Constraints

- Option B: the value reaches the reports through the CLI-built report wirings (`ExportReportWiring`, `JsonReportWiring`, `HtmlReportWiring`) as an optional constructor parameter and is rendered by the adapters only when present. `ReportInputDTO` does not change. FastAPI keeps calling the wirings with no arguments.
- `AnalyzeDocumentUseCaseWiring` receives the prompts root as a constructor parameter (default: the packaged root); the two directory constants `PROMPTS_DIR` remain and stay valid.
- Follow `.agent/skills/clean-architecture/SKILL.md`: no inline comments, PEP 257 docstrings, one class per file, tests inherit `unittest.TestCase`, adapters instantiated only in wirings, no abbreviations.

## 4. Tasks

- [x] **TASK-01** Rename the `v2` prompt files (drop `_v2`) and add a `PROMPTS_ROOT` constant for the packaged root. `AnalyzeDocumentUseCaseWiring` accepts `prompts_root` (default packaged) and derives `classification/` and `quality/` from it; `OverridableAnalyzeDocumentUseCaseWiring` forwards it. RED first.
- [x] **TASK-02** `CommandLineArguments.prompts_directory` and the `--prompts-dir` option with strict validation of the six files in the parser; plumb the value `DocumentAnalysisCommand` -> services factory -> `DocumentAnalysisCommandWiring` -> `CliAnalysisServicesWiring` -> `OverridableAnalyzeDocumentUseCaseWiring`. RED first.
- [x] **TASK-03** Prompt source description: a value object built from `CommandLineArguments` (`default` or root folder name, plus replaced prompt names in fixed order) with its text rendering; log it from the CLI run. RED first.
- [ ] **TASK-04** Show the prompt source in the reports: optional parameter in `ExportReportWiring`, `JsonReportWiring` and `HtmlReportWiring`, rendered by the Word, JSON and HTML adapters only when present; `CliAnalysisServicesWiring` passes it, FastAPI does not. RED first.
- [ ] **TASK-05** README usage for `--prompts-dir` and the reported prompt source; full unit-suite run.

## 5. Open items

- "Log" is implemented as the standard `logging` output configured by `LoggingConfigWiring` (the CLI also has the console `ConsoleStepAnnouncer`, which is left untouched). Confirm with the user at close.

## 6. Evidence

### TASK-01
- RED: `PROMPTS_ROOT` import failed with `ImportError`; then `test_create_use_case_reads_prompt_templates_from_custom_prompts_root` and `test_create_use_case_loads_renamed_v2_prompt_set_from_its_root` (analyze wiring) and `test_create_use_case_reads_prompt_templates_from_custom_prompts_root` and `test_per_prompt_override_wins_over_custom_prompts_root` (overridable wiring) failed with `TypeError: unexpected keyword argument 'prompts_root'`.
- GREEN: 61 focused tests passing (re-run by the parent); full unit suite `Ran 2201 tests, OK` (reported by the writer).
- `prompts_root` stays a regular trailing parameter, like `prompt_file_overrides`.
- Commit: `ec996d0` `feat(prompts): read prompts from a configurable root in the wirings`.

### TASK-02
- RED: 10 errors and 3 failures, e.g. `test_usage_error_names_first_missing_file_in_prompt_order` (`unrecognized arguments: --prompts-dir`), `test_passes_prompts_directory_to_services_factory` (`TypeError`), `test_services_factory_forwards_prompts_root`, `test_prompt_root_relative_paths_lists_six_files_grouped_by_folder` (`AttributeError`). Caveat: the rejection tests passed in RED because argparse already rejected the unknown option; their real signal comes with the positive and message tests.
- GREEN: 107 focused tests passing (re-run by the parent); full unit suite `Ran 2215 tests, OK` and ruff clean (reported by the writer).
- The six expected files live only in `CommandLineArguments.prompt_root_relative_paths()`; the missing-file message uses the POSIX form (`classification/s4_s5_s6_signal_prompt.txt`).
- Commit: `2a2f883` `feat(cli): add --prompts-dir to replace the whole prompts root`.
- The services factory now takes a third argument `prompts_root`; `CliAnalysisServicesWiring` already holds both `prompt_file_overrides` and `prompts_root`, which is all TASK-03 needs to describe the prompt source.

### TASK-03
- RED: `ModuleNotFoundError` for the DTO and the builder; 42 `TypeError` (`unexpected keyword argument 'prompt_source'`) and 4 `AttributeError` for the new `CliAnalysisServices` field; `test_logs_prompt_source_description_once_per_run` and `test_logs_default_prompt_source_when_no_custom_prompts_are_used` failed with `no logs of level INFO or higher triggered on root`. `test_prompt_source_is_not_printed_to_console` is a guard that passed from the start.
- GREEN: 81 focused tests passing (re-run by the parent); full unit suite `Ran 2239 tests, OK` and ruff clean (reported by the writer).
- `PromptSourceDTO.describe()` yields `default`, `v2`, `default + a, b`, `v2 + a`. `PromptSourceBuilder` is instantiated only in `CliAnalysisServicesWiring`; the base label is `prompts_root.resolve().name`.
- Log: `logger.info("Prompt source: %s", ...)` after the services are created. `LOG_LEVEL` is required by `EnvConfig` and `.env`/`.env.example` set it to INFO. The only root handler is the rotating file, so the line is NOT printed on the console (spec open item in section 5).
