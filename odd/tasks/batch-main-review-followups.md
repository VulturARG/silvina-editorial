# Feature: Batch Runner Review Follow-ups (R3 findings)

- **Feature Name**: `batch-main-review-followups`
- **File Locator**: `odd/tasks/batch-main-review-followups.md`
- **Branch**: `feat/batch-main`
- **TDD Mode**: Test-first (RED then GREEN); one small test per fix, no redundant tests
- **TDD Runner**: `export APP_MODE=PROD; .venv/Scripts/python.exe -m unittest discover -s src -t . -p "test_*.py"` and the same with `-s tests`
- **Commit policy**: one work-unit commit per task (Conventional Commits); push, PR and merge stay the user's decisions

---

## 1. Objective

Address the advisory findings R3-001..R3-007 of the approved native review of `batch-main` (lineage `review-16729332daf21124`, medium risk, lens `review-reliability`, authority burned). The findings are non-blocking and were delivered as location and severity only; the readings below are the author's, not the reviewer's text.

## 2. Findings and decisions

| ID | Location | Reading | Fix |
|---|---|---|---|
| R3-001 | `batch_file_reader.py:83` | A `name` key in `[batch]` reaches `CommandLineArguments` and fails with an unclear `TypeError`. | Reject it with a clear `ValueError` (it belongs to each `[[run]]`). |
| R3-002 | `batch_runner.py:37` | An exception raised by the command is not tied to a run and document in the console. | Announce the run and document, then re-raise the same exception. |
| R3-003 | `batch_file_reader.py:98` | The external-LLM guard tests truthiness; the text `"false"` counts as true. | Require a boolean `use_external_llm`, rejecting other types with a clear `ValueError`. |
| R3-004 | `batch_file_reader.py:110-111` | `app_mode` with surrounding spaces is rejected although `EnvConfig` strips it. | Strip before comparing. |
| R3-005 | `test_batch_sample_files.py:22-26` | The test hardcodes 15 documents and breaks when an input is added. | Expect the sorted `.docx` names found in the inputs folder (no `~$`). |
| R3-006 | `batch_two_documents.toml:13-18` | The sample uses Claude when run as is. | Handled manually by the user; out of scope. |
| R3-007 | `batch_file_reader.py:69` | An unknown field fails with the dataclass `TypeError` without the run name. | Wrap it in a `ValueError` that names the run. |

## 3. Tasks

- [x] **TASK-01: Reader fixes (R3-001, R3-003, R3-004, R3-007)**
  - **Scope**: `batch_file_reader.py` and `test_batch_file_reader.py`.
  - **Outcome**: `name` in `[batch]` is rejected, `use_external_llm` must be a bool, `app_mode` is compared stripped, and a field that is not a command line argument fails with a `ValueError` naming the run (RED 5 failures in 4 tests, GREEN 14). Commit `40461f2`.
- [x] **TASK-02: Runner context for exceptions (R3-002)**
  - **Scope**: `batch_runner.py` and `test_batch_runner.py`.
  - **Outcome**: An exception raised by the command is announced with the run and document and re-raised unchanged; `KeyboardInterrupt` is untouched (RED 1 failure, GREEN 6). Commit `f2fd70f`.
- [x] **TASK-03: Sample files test independent of the input count (R3-005)**
  - **Scope**: `test_batch_sample_files.py`.
  - **Outcome**: The expected documents come from the sorted `.docx` names of the inputs folder, no hardcoded 15. Commit `661183f`.

## 4. Verification

`src` 2367 and `tests` 34 OK, ruff and pyright clean on the touched files. R3-006 was left to the user.
