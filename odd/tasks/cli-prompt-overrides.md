# Feature: CLI Prompt File Overrides

- **Feature Name**: `cli-prompt-overrides`
- **File Locator**: `odd/tasks/cli-prompt-overrides.md`
- **Branch**: `feat/cli-prompt-overrides` (from `feat/cli-document-analysis`, which is where the command line `main.py` lives)
- **TDD Mode**: Enabled (RED -> GREEN -> REFACTOR) where a runnable test applies
- **TDD Runner**: `.venv/Scripts/python -m unittest discover -s src -t . -p "test_*.py"` with `USE_EXTERNAL_LLM=false APP_MODE=PROD`
- **Delivery Strategy**: stop before every commit and wait for the user's instructions

---

## 1. Objective

Let `main.py` receive six optional arguments, each one the directory that contains the `.txt` file replacing the matching default prompt of the system.

## 2. Agreed specification

- Six new optional arguments, one per default resource under `src/infrastructure/resources/prompts/`: `s4_s5_s6_signal_prompt`, `alignment_prompt`, `argumentation_conclusions_prompt`, `clarity_coherence_prompt`, `contribution_prompt`, `research_lines`.
- Command line flags use the kebab-case style of the existing options: `--s4-s5-s6-signal-prompt`, `--alignment-prompt`, `--argumentation-conclusions-prompt`, `--clarity-coherence-prompt`, `--contribution-prompt`, `--research-lines`.
- Each value is a DIRECTORY path; the system appends the file name `<argument>.txt` (for example `--alignment-prompt C:\prompts` reads `C:\prompts\alignment_prompt.txt`). When the argument is given, its content replaces the matching default prompt; when it is omitted the default stays.
- A path that is not an existing directory, or that does not contain the expected `<argument>.txt`, is a usage error reported by the argument parser, before anything runs.
- The argument is a directory and the file name is fixed by the system (user decision, third and final interpretation of "a file with the same name and the .txt extension").

## 3. Constraints

- Overrides are file paths, not environment variables: they do not go through `OverridableEnvConfig`.
- `AnalyzeDocumentUseCaseWiring` gets one protected hook `_read_prompt_text(directory, filename)` used by the six read sites; `OverridableAnalyzeDocumentUseCaseWiring` overrides it.
- The `research_lines` read currently goes through `FileGatewayAdapter().read(join(...))`; it moves to the same hook (same UTF-8 read).

## 4. Tasks

- [x] **TASK-01** `CommandLineArguments` gets the six `Path | None` fields and `prompt_file_overrides()`; `CommandLineArgumentParser` declares the six options with existing-directory and expected-file validation. RED first.
- [x] **TASK-02** `_read_prompt_text` hook in `AnalyzeDocumentUseCaseWiring`; `OverridableAnalyzeDocumentUseCaseWiring` accepts `prompt_file_overrides` and replaces the matching prompt. RED first.
- [x] **TASK-03** Plumb the overrides: `DocumentAnalysisCommand` -> services factory -> `DocumentAnalysisCommandWiring` -> `CliAnalysisServicesWiring`; update the affected tests; README usage.

## 5. Open items

- None.

## 6. Evidence

### TASK-01
- RED: `test_prompt_file_overrides_maps_given_paths_to_field_names`, `test_prompt_file_overrides_maps_omitted_values_to_none`, `test_prompt_file_overrides_exposes_only_the_six_prompt_keys` failed with `AttributeError` / `TypeError`. Parser tests failed with `SystemExit: 2` (unrecognized arguments).
- GREEN: 7 tests in `test_command_line_arguments.py` and 29 tests in `test_command_line_argument_parser.py` passing.

### TASK-02
- RED: `test_read_prompt_text_reads_text_resource` failed with `AttributeError: 'AnalyzeDocumentUseCaseWiring' object has no attribute '_read_prompt_text'`. `OverridableAnalyzeDocumentUseCaseWiring` prompt override tests failed with `TypeError: unexpected keyword argument 'prompt_file_overrides'`.
- GREEN: 44 tests in `test_analyze_document_use_case_wiring.py` and 15 tests in `test_overridable_analyze_document_use_case_wiring.py` passing.

### TASK-03
- RED: `test_passes_environment_overrides_of_arguments_to_services_factory` and `test_passes_prompt_file_overrides_to_services_factory` failed because `_services_factory` expected 2 arguments instead of 1. `test_services_factory_forwards_environment_and_prompt_file_overrides` failed with `TypeError`.
- GREEN: 22 tests in `test_document_analysis_command.py`, 2 tests in `test_document_analysis_command_wiring.py`, and 8 tests in `test_cli_analysis_services_wiring.py` passing. All 2030 unit tests across `src` and 10 tests across `tests/` passing.
