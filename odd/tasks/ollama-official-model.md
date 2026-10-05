# Feature: Official Ollama Model (gemma4-26b-adapted) and Version 0.100

- **Feature Name**: `ollama-official-model`
- **File Locator**: `odd/tasks/ollama-official-model.md`
- **Branch**: `feat/ollama-official-model` (from `silvina_editorial_v100` at `6816643`)
- **TDD Mode**: Test-first where a deterministic runner applies (Modelfile content test, `EnvConfig` default); scripts and docs get structural or functional verification
- **TDD Runner**: `export USE_EXTERNAL_LLM=false APP_MODE=PROD; .venv/Scripts/python.exe -m unittest discover -s src -t . -p "test_*.py"` (the repo `.env` points to Claude, hence the overrides)
- **Delivery Strategy**: `ask-on-risk`
- **Commit policy**: three work-unit commits on the feature branch plus a final `docs(odd)` commit (the identities are recorded here after they exist); push, PR and merge only on the user's express order
- **Out of the working tree scope**: `odd/tasks/real-run-findings.md` and `openspec/changes/archive/2026-06-23-classify-article/tasks.md` were already modified before this feature; they are never staged here

---

## 1. Objective

Make `gemma4-26b-adapted` the official Ollama model (decision of 2026-10-04, Engram `decision/official-ollama-model`) and make it reproducible, and bump the application version to `0.100`.

Why: the raw `hf.co/unsloth/gemma-4-26B-A4B-it-GGUF:UD-IQ4_XS` declares no `thinking` capability (`ollama show`), so `OLLAMA_THINK=false` cannot work on it and thinking tags leak into the answers. `gemma4-26b-adapted` has the same weights (same blobs) plus `RENDERER gemma4`, `PARSER gemma4` and a template that closes the thought channel. It only existed inside one local Ollama; the original Modelfile (OpenArma `scratch/Modelfile`) is gone.

## 2. Design decisions

- The Modelfile lives in `src/infrastructure/resources/ollama/gemma4-26b-adapted.Modelfile`, with an `__init__.py` exposing `MODELFILE_DIR` like the prompts packages, so it is testable with `read_text_resource`.
- It is a faithful reproduction of the current model (`ollama show gemma4-26b-adapted --modelfile`), with the two blob `FROM` lines replaced by the portable tag `FROM hf.co/unsloth/gemma-4-26B-A4B-it-GGUF:UD-IQ4_XS`. No optimization.
- `scripts/create_ollama_model.bat` pulls the base ONLY when it is missing (`ollama show` check) and runs `ollama create`; optional first argument overrides the model name so it can be verified without touching the real one. Minimum Ollama version documented: 0.35.0. (First version pulled unconditionally; see the incident in section 5.)
- Version is a plain string in `version.txt`: `0.100` (user order 2026-10-04). `main.py` still says `v0.9`; left out on purpose (the CLI is under separate analysis).

## 3. Tasks

- [x] **TASK-01: Versioned Modelfile and its package**
  - **Scope**: `src/infrastructure/resources/ollama/__init__.py` (`MODELFILE_DIR`), `gemma4-26b-adapted.Modelfile`, test in `src/infrastructure/tests/test_ollama_modelfile.py`.
  - **Verification**: RED first (file missing); then GREEN: starts with `FROM hf.co/...`, contains `RENDERER gemma4`, `PARSER gemma4`, the thought-channel closing in the template, both `stop` parameters.
- [x] **TASK-02: Creation script**
  - **Scope**: `scripts/create_ollama_model.bat`.
  - **Verification**: functional. `ollama create gemma4-26b-adapted-check -f <Modelfile>`, then `ollama show --modelfile` of both models must match (except the header comment); `ollama rm gemma4-26b-adapted-check` afterwards. The model is never loaded on the GPU.
  - **Commit 1**: `feat(llm): version the gemma4-26b-adapted Modelfile and its creation script` (`334c232`)
  - **Extra (not in the original plan)**: `.gitattributes` rule `*.Modelfile text eol=lf` plus a byte-level test, because git autocrlf on Windows could put a CR inside the multi-line TEMPLATE.
- [x] **TASK-03: Default model name**
  - **Scope**: `src/infrastructure/env_config.py`, `src/infrastructure/tests/test_env_config.py`.
  - **Verification**: RED (update the expected default in the test, it fails), then GREEN.
  - **Outcome**: RED observed with the project runner (`unittest discover`): 1 failure, `'hf.co/unsloth/...' != 'gemma4-26b-adapted'`. (Invoking the module directly shows 26 extra errors for the missing `METRICS_DATABASE_PATH`; they exist without this change too.) GREEN: 60 tests OK, ruff check and format clean.
- [~] **TASK-04: Documentation of the model** (partial: `.env.example` pending, see section 5)
  - **Scope**: `.env.example`, `README.md` (header line 19 and the installation step at lines 208-209, with `ollama create` and the minimum Ollama version), `openspec/specs/analyze-document/spec.md` (table row of `OLLAMA_MODEL_NAME`).
  - **Verification**: structural: no remaining mention of the raw model as the official one (grep).
  - **Outcome**: README (header, installation step with the script and the manual equivalent, upstream drift caveat) and the spec row updated; the only remaining mentions of the raw GGUF are the base-model references. `.env.example` was NOT edited: the edit tool was blocked by the Gentle AI safety policy for that sensitive path and it was not bypassed.
  - **Commit 2**: `feat(config): make gemma4-26b-adapted the default Ollama model` (`d8d1380`)
- [x] **TASK-05: Version 0.100**
  - **Scope**: `version.txt` (`0.95` -> `0.100`), `README.md` lines 1, 3 and 17.
  - **Verification**: `EnvConfig` reads `0.100` from the real file; grep for stale `0.95` as an application version.
  - **Plan correction**: the plan said the suite would be unaffected. It was not: `test_defaults_are_loaded_when_env_is_empty` reads the REAL `version.txt` and hardcoded `"0.95"`, so it failed (`'0.100' != '0.95'`). Its expectation and the spec scenario quoting the file content moved to `0.100`. The test stays coupled to the real file: every future bump breaks it again. My first grep was also truncated by `head -40` and missed the README footer (`**Version:**`, line 423); found afterwards.
  - **Left untouched on purpose**: README changelog and roadmap headings that still say `v0.95` (lines 305, 354, 366), including `### v0.95 (Q2 2026) — Current`; the `(Q2 2026)` label next to the current version; `main.py` (`v0.9`).
  - **Commit 3**: `chore(release): bump the application version to 0.100` (`c44db3f`)

## 3b. Follow-ups requested by the user (2026-10-04, second round)

- [x] **TASK-06: Commit the `.env.example` edit** (`1f1adbc`) the user made by hand (the edit tool is blocked on that path). Old line kept as a comment, new line `OLLAMA_MODEL_NAME=gemma4-26b-adapted`.
- [x] **TASK-07: Fix the fragile version test** (`d23a09d`; verified by simulating a bump: with `version.txt` = `9.9.9` the 61 tests of the module stay green). `test_defaults_are_loaded_when_env_is_empty` read the REAL `version.txt` and hardcoded its value. Inject a temporary version file by patching `_VERSION_FILE_PATH` in a dedicated test; the defaults test stops asserting the version. No meaningful RED (the behavior already exists; this decouples the test), so the check is that bumping `version.txt` no longer breaks it.
- [x] **TASK-08: Stale version references in `main.py` and the README** (`6629123`; RED observed: banner showed `v0.9` instead of `v7.7.7`; GREEN: 49 tests in `tests/`). `main.py` prints the version from `EnvConfig().silvina_version` (single source: `version.txt`) instead of a hardcoded `v0.9` (test first: banner shows `SILVINA_VERSION` under `TESTING`). README: Version History, Roadmap, footer (`Last Updated`, `Active Branch`), based on the first-parent history, nothing invented.
- [x] **TASK-09: Commit the two pre-existing Markdown files** (`7913b25`, `24ab01f`) (`odd/tasks/real-run-findings.md`, archived `classify-article/tasks.md`) as separate docs commits, as the user ordered. Their diffs are path rewrites (`src/...` -> `../../src/...`), not new content.
- README beyond the version: besides the version and branch references, the README had instructions that no longer work (`python gradio_app.py`; the file does not exist), so the startup command, the tagline, the technology table and the project tree entry were fixed. NOT fixed because they cannot be verified from the code: the feedback file `_feedback.json` "via Gradio" (line ~172) and the "Structured expert feedback panel (8 evaluation fields)" bullets; the v0.9 history entry that mentions Gradio is history. `(Q4 2026)` next to the current version is the current quarter, not a verified release date.
- Warm-up and `keep_alive` (design pending the user's confirmation) and the discussion about deleting the duplicated base model are NOT part of these tasks; the latter is explanation only, nothing implemented.

## 4. Excluded on purpose

1. Experiment with a minimal Modelfile (`FROM` + `RENDERER` + `PARSER` only): needs loading the model on the GPU, authorized separately.
2. Error message with creation instructions when the model is missing: the domain must not know Ollama; needs its own design decision.
3. Revisit Engram #2438 (raw model as Laya teacher).
4. `main.py` header `v0.9`.

## 5. Evidence log

### TASK-01 / TASK-02 (2026-10-04)

- RED observed: `ModuleNotFoundError: No module named 'src.infrastructure.resources.ollama'`; GREEN: 6 tests OK; full suite reported by the worker: 1426 passed. Commit hooks (trailing whitespace, end of files, ruff, ruff format) passed.
- Functional check with the temporary model `gemma4-26b-adapted-check` (created from the versioned Modelfile, never loaded on the GPU, removed afterwards; `ollama list` confirms the real model untouched). `ollama show --modelfile` of the real and the temporary model differ ONLY in the name comment and in the base weights blob line; TEMPLATE, RENDERER, PARSER and stop parameters are identical; capabilities identical (`thinking` false/true).
- Script error path: without `ollama` on PATH it prints the error and exits 1.

### Final verification (gentle-ai-verify, 2026-10-04)

- `unittest discover -s src`: 1426 tests OK (1420 baseline + 6). `unittest discover -s tests`: 48 tests OK. `ruff check` and `ruff format --check` on the changed Python files: clean. No `ollama` command was run by the verifier.
- Not covered by an automated test: the batch script and the real `ollama create`; both were verified by hand with the temporary model (above).

### Final verification, second round (gentle-ai-verify, 2026-10-04)

- `unittest discover -s src`: 1427 tests OK (1426 + the dedicated version test). `unittest discover -s tests`: 49 tests OK. `ruff check` and `ruff format --check` on the 6 Python files changed since `6816643`: clean. The `ERROR: 'ValueError' exception was raised ... AnalyzeDocumentUseCase` line in the output is a log emitted by `@generic_error_handler` in a test that provokes it on purpose, not a failure.
- No test asserts the content of the real `version.txt` any more: the version tests inject a temporary file or use the `TESTING` fallback.
- Not verified: a real version bump (the verifier cannot edit files; the bump was simulated by hand earlier with `9.9.9`).

### Native review

- First candidate (the two pre-existing Markdown files): reviewed with `review-reliability`, outcome `approved`, authority burned. It did not include this feature's commits.
- Second candidate (this file, documentation only): not started on purpose; the review contract allows skipping a trivial passive documentation-only edit. The committed range `6816643..HEAD` has not been reviewed; it can be requested with `baseRef` and `committedOnly`.

### Incident: the first script version pulled the base unconditionally

- I had told the worker the pull would be a no-op because the base was already installed. It was NOT: the Hugging Face manifest of `hf.co/unsloth/gemma-4-26B-A4B-it-GGUF:UD-IQ4_XS` had moved, so `ollama pull` downloaded a new 13.6 GB blob (`babd1e38...`, 2026-10-04 20:36) and repointed the base model (ID `7cf78edc47c4` -> `5918a78562ec`).
- Consequences: `gemma4-26b-adapted` still uses the old blob (`694a7d2a...`), so both blobs sit on disk (~13.6 GB extra on E:, 64 GB free). The raw base model installed on this machine is no longer the one it had for 4 months.
- Fix: the script now pulls only when `ollama show` fails; re-verified: running it left the base manifest untouched.
- Reproducibility caveat: a `FROM hf.co/...` tag is a moving target. A model rebuilt today uses different weights bytes than the one validated in the earlier real runs (same size to the displayed precision; nature of the difference not inspected). The real `gemma4-26b-adapted` was NOT recreated; that is a user decision.
