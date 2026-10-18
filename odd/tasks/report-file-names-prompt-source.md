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
- The word `default` NEVER appears in the file name. With no custom root and no replaced prompts, the name is exactly as today.
- Examples with model `claude-haiku-5-5`: `doc_analisis_claude-haiku-5-5` (all default); `..._v2`; `..._v2+alignment_prompt`; `..._clarity_coherence_prompt+research_lines` (default root, two replaced prompts).
- `+` is valid in file names on Windows, Linux and macOS, and `WindowsFileNameSanitizer` does not touch it; each part still goes through the sanitizer.
- The same suffix applies to the three reports (`.docx`, `.json`, `.html`). The web flow is not affected.

## 3. Constraints

- `ReportFilePathsBuilder.build` keeps working when no prompt source is given (optional parameter) so existing callers and tests are not forced to change.
- `PromptSourceDTO` already has `base_label` (`default` or the root folder name) and `replaced_prompt_names`; reuse it, do not add file name concerns to the domain DTO.
- Follow `.agent/skills/clean-architecture/SKILL.md`.

## 4. Tasks

- [x] **TASK-01** `ReportFilePathsBuilder.build` accepts an optional prompt source and appends the suffix; `DocumentAnalysisCommand` passes `services.prompt_source`; README documents the new names. RED first.

## 5. Open items

- Windows path length: the suffix with the six per-prompt names is about 100 characters longer than today; mention it to the user at close.

## 6. Evidence

### TASK-01
- RED: 11 `TypeError: ReportFilePathsBuilder.build() takes 4 positional arguments but 5 were given` (one per case with a prompt source) and `test_exports_reports_with_prompt_source_suffix_in_their_names` (paths without the suffix). `test_default_prompt_source_keeps_report_names_without_suffix` is a characterization test that passed from the start.
- GREEN: 63 focused tests passing (re-run by the parent); full unit suite `Ran 2267 tests, OK`; ruff clean (reported by the writer).
- The parent also computed the real names: `doc_analisis_claude-haiku-5-5` (no source and default source), `..._v2`, `..._v2+alignment_prompt` and `..._clarity_coherence_prompt+research_lines`, all as specified.
- README documents the suffix with three examples.
