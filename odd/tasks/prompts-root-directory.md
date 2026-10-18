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
- [ ] **TASK-02** `CommandLineArguments.prompts_directory` and the `--prompts-dir` option with strict validation of the six files in the parser; plumb the value `DocumentAnalysisCommand` -> services factory -> `DocumentAnalysisCommandWiring` -> `CliAnalysisServicesWiring` -> `OverridableAnalyzeDocumentUseCaseWiring`. RED first.
- [ ] **TASK-03** Prompt source description: a value object built from `CommandLineArguments` (`default` or root folder name, plus replaced prompt names in fixed order) with its text rendering; log it from the CLI run. RED first.
- [ ] **TASK-04** Show the prompt source in the reports: optional parameter in `ExportReportWiring`, `JsonReportWiring` and `HtmlReportWiring`, rendered by the Word, JSON and HTML adapters only when present; `CliAnalysisServicesWiring` passes it, FastAPI does not. RED first.
- [ ] **TASK-05** README usage for `--prompts-dir` and the reported prompt source; full unit-suite run.

## 5. Open items

- "Log" is implemented as the standard `logging` output configured by `LoggingConfigWiring` (the CLI also has the console `ConsoleStepAnnouncer`, which is left untouched). Confirm with the user at close.

## 6. Evidence

### TASK-01
- RED: `PROMPTS_ROOT` import failed with `ImportError`; then `test_create_use_case_reads_prompt_templates_from_custom_prompts_root` and `test_create_use_case_loads_renamed_v2_prompt_set_from_its_root` (analyze wiring) and `test_create_use_case_reads_prompt_templates_from_custom_prompts_root` and `test_per_prompt_override_wins_over_custom_prompts_root` (overridable wiring) failed with `TypeError: unexpected keyword argument 'prompts_root'`.
- GREEN: 61 focused tests passing (re-run by the parent); full unit suite `Ran 2201 tests, OK` (reported by the writer).
- `prompts_root` stays a regular trailing parameter, like `prompt_file_overrides`.
- Commit: see `git log` entry `feat(prompts): read prompts from a configurable root in the wirings`.
