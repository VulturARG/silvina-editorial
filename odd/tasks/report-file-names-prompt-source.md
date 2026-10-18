# Feature: Prompt Source in the Report File Names (CLI)

- **Feature Name**: `report-file-names-prompt-source`
- **File Locator**: `odd/tasks/report-file-names-prompt-source.md`
- **Branch**: `feat/report-file-names-prompt-source` (chained on `feat/prompts-root-directory`, open PR #111, because it uses `PromptSourceDTO`)
- **TDD Mode**: Enabled (RED -> GREEN -> REFACTOR) where a runnable test applies
- **TDD Runner**: `.venv/Scripts/python -m unittest discover -s src -t . -p "test_*.py"` with `USE_EXTERNAL_LLM=false APP_MODE=PROD`
- **Delivery Strategy**: one work-unit commit per task on the feature branch; push, pull request and merge stay with the user

---

## 1. Objective

A CLI run that uses a non-default prompt source must not overwrite the reports of a run with the default prompts: the report file names carry the prompt source.

## 2. Agreed specification

- The base name stays `<document>_analisis_<model>`. When the run has a non-default prompt source, a suffix is appended: `_` followed by the parts joined with `+`.
- Parts, in this order: (1) the name of the `--prompts-dir` folder, without its path, when the flag is used; (2) the names of the prompts replaced with per-prompt flags, in the fixed order of `CommandLineArguments.PROMPT_NAMES`.
- The word `default` never appears in the file name for the default source (a custom root folder that happens to be named `default` is shown as `_default`, see TASK-02). With no custom root and no replaced prompts, the name is exactly as today.
- Examples with model `claude-haiku-5-5`: `doc_analisis_claude-haiku-5-5` (all default); `..._v2`; `..._v2+alignment_prompt`; `..._clarity_coherence_prompt+research_lines` (default root, two replaced prompts).
- `+` is valid in file names on Windows, Linux and macOS, and `WindowsFileNameSanitizer` does not touch it; each part still goes through the sanitizer.
- The same suffix applies to the three reports (`.docx`, `.json`, `.html`). The web flow is not affected.

## 3. Constraints

- `ReportFilePathsBuilder.build` keeps working when no prompt source is given (optional parameter) so existing callers and tests are not forced to change.
- `PromptSourceDTO` already has `base_label` (`default` or the root folder name) and `replaced_prompt_names`; reuse it, do not add file name concerns to the domain DTO.
- Follow `.agent/skills/clean-architecture/SKILL.md`.

## 4. Tasks

- [x] **TASK-01** `ReportFilePathsBuilder.build` accepts an optional prompt source and appends the suffix; `DocumentAnalysisCommand` passes `services.prompt_source`; README documents the new names. RED first.

- [x] **TASK-02** The suffix depends on whether `--prompts-dir` was used, not on the folder name: `PromptSourceDTO` gets an explicit `uses_custom_prompts_root: bool = False` set by `PromptSourceBuilder` when a root is given; `ReportFilePathsBuilder` uses it instead of comparing the label with `default`. A root folder literally named `default` now gets the suffix `_default` and no longer overwrites the default reports. RED first.

## 5. Open items

- Native review of TASK-01 (commit `5239ecc`, 6 files, 245 lines) was approved and acknowledged (lineage `review-a43fe7d3b0280997`, medium risk, lens `review-reliability`, authority burned). Advisory findings, non-blocking, location only (the provider returns no text): R3-001 and R3-004 WARNING `report_file_paths_builder.py:58`, R3-003 WARNING `:63`, R3-002 WARNING `:67`, R3-005 WARNING `test_document_analysis_command.py:159`. Separate later work. One edge case reasoned by the parent, not confirmed by the findings: a `--prompts-dir` folder literally named `default` is treated as the default source, so its reports get no suffix and overwrite the default ones.
- Commit and branch are local: this branch is not pushed and has no pull request.

- Windows path length: the suffix with the six per-prompt names is about 100 characters longer than today; mention it to the user at close.

## 6. Evidence

### TASK-01
- RED: 11 `TypeError: ReportFilePathsBuilder.build() takes 4 positional arguments but 5 were given` (one per case with a prompt source) and `test_exports_reports_with_prompt_source_suffix_in_their_names` (paths without the suffix). `test_default_prompt_source_keeps_report_names_without_suffix` is a characterization test that passed from the start.
- GREEN: 63 focused tests passing (re-run by the parent); full unit suite `Ran 2267 tests, OK`; ruff clean (reported by the writer).
- The parent also computed the real names: `doc_analisis_claude-haiku-5-5` (no source and default source), `..._v2`, `..._v2+alignment_prompt` and `..._clarity_coherence_prompt+research_lines`, all as specified.
- README documents the suffix with three examples.

### TASK-02
- RED: 17 errors of 89 tests (`TypeError`/`AttributeError`, the field did not exist). The `default` folder bug itself was masked by the missing constructor argument, so it was never seen failing by assertion; `test_default_source_without_custom_root_flag_adds_no_suffix` is a characterization test.
- GREEN: 114 focused tests passing (re-run by the parent); full unit suite `Ran 2276 tests, OK`; ruff clean (reported by the writer). Eight existing tests were adapted to pass `uses_custom_prompts_root=True` (seven in `test_report_file_paths_builder.py`, one in `test_document_analysis_command.py`); their expected names did not change.
- The parent also computed the real names: no root `doc_analisis_claude-haiku-5-5`; root `v2` `..._v2`; root named `default` `..._default`; root named `default` plus `alignment_prompt` `..._default+alignment_prompt`; no root plus two prompts `..._clarity_coherence_prompt+research_lines`.
- `describe()` is unchanged, so the log and the reports still print `default` for a custom root named `default`; only the file names tell the two apart.
