# Feature: Real-Run Findings (Classification References, LLM Reasoning, Web Flow)

- **Feature Name**: `real-run-findings`
- **File Locator**: `odd/tasks/real-run-findings.md`
- **TDD Mode**: Enabled (Strict TDD: RED -> GREEN -> REFACTOR)
- **TDD Runner**: `.venv/Scripts/python -m pytest -q` (whole repository: `src/` and `tests/`)
- **Delivery Strategy**: `ask-on-risk` (one branch and one PR per task, from `silvina_editorial_v100`; merge commits; no commit or push without explicit user authorization)
- **Forecast Changed Lines**: not estimated yet (per task, see section 4)
- **Running Authored Lines**: 0
- **Status**: findings documented; TASK-01 and TASK-02 delivered (PR #54, PR #55); every other task is a proposal awaiting a user decision.

---

## 1. Objective & Problem
While exercising the application with real documents on 2026-10-01 (CLI and web, Ollama 0.35.0, model `hf.co/unsloth/gemma-4-26B-A4B-it-GGUF:UD-IQ4_XS` and the locally created `gemma4-26b-adapted`, GPU RX 7800 XT 16 GB), the audit tooling delivered by `internal-metrics-and-ai-audit` (metrics database, rotating log, request middleware, prompt/response audit) made it possible to inspect each analysis end to end. That inspection exposed defects that were invisible before: some inside the LLM integration, some in the classification logic, some in the web flow.

This document records every finding with its evidence, root cause, impact and a proposed action, so each one can be accepted, scheduled or rejected explicitly. It does NOT authorize any change by itself.

Test document used throughout: `capacidades_razonamiento_emergente_LLMs.docx` (3,613 words, 26,235 characters, 34 references, 28 in-text citations).

---

## 2. Findings

### F-01 (HIGH, OPEN) Signals S2a and S2b can never be satisfied: `DocumentContentDTO.references` is always empty
- **Symptom**: a systematic review with 34 references is classified `DIVULGACION` with no confidence (`Confianza: -`) and the reasoning "carece del respaldo bibliografico minimo (S2a y S2b ausentes)", while the same report shows 34 references and a 96.4 % citation match.
- **What the model was asked**: nothing about S2a/S2b. The only classification prompt (`src/infrastructure/resources/prompts/classification/s4_s5_s6_signal_prompt.txt`) asks S4, S5 and S6. For the analyzed document the model answered `S4: SI`, `S5: SI`, `S6: SI` (14 tokens, 6.5 s, well formed).
- **Where S2a/S2b come from**: `src/domain/classification/reference_signal_detector.py` computes them from `document_content.references`: S2a = at least 12 references; S2b = at least 50 % of references with a year >= current year - 4 (regex on the reference text).
- **Root cause**: `src/infrastructure/adapters/document/paragraph_content_adapter.py:39` builds `DocumentContentDTO(..., references=[], ...)` unconditionally, so both signals are always `False`, for every document. The 34 references shown in the report come from a different path (`CitationExtractor` / `DocxReferenceAdapter`) that never feeds the DTO the classifier receives.
- **Verification against `main` (legacy, `silvina_editorial_v09`)**:
  - The algorithm is identical: `business_logic/article_classifier.py` `_signal_reference_count` (`>= 12`) and `_signal_reference_recency` (`>= 50 %`, year `>= now - 4`, same regex).
  - In `main` the list WAS populated: `data_access/content_extractor.py` `extract_content(paragraphs, docx_path)` step 5 calls `ReferenceParser().parse_from_docx(docx_path)`, and `main.py:117` passes the document path.
- **How it was lost (history)**: 2026-06-13 `domain-foundations` defines `DocumentContentDTO.references`; 2026-06-23 `classify-article` ports S2a/S2b reading that field; 2026-06-26 `extract-content` decides "`references=[]` always (break ReferenceParser coupling) - references are a future slice" and its spec requires `references MUST equal []`; 2026-06-26 `extract-citations` creates the reference extractor; the integration between the two was never made. The parity smoke test `tests/smoke/test_extract_content_parity.py` does not check references.
- **Reproduction** (offline, with the model's real answer): `references=[]` -> `POPULAR_SCIENCE`, confidence `None`; with the 34 references -> `SCIENTIFIC`, `FULL_SIGNAL_MATCH` (34 >= 12; 22 of 34 = 65 % with year >= 2022). Recipe: build the wiring, call `_get_document_content_extractor().extract_content(...)` and `_get_citation_extractor().extract_citations_and_references(...)`, replace the classifier's `_llm_generator` with a stub returning `S4: SI\nS5: SI\nS6: SI`, and classify with `dataclasses.replace(content, references=references)`.
- **Impact**: wrong category for any document whose classification depends on references; the category drives which sections the structure validation requires (`effective_structure_type`) and which recommendations are emitted; empty confidence in the report.
- **Proposed action**: populate the references where the DTO is assembled (domain service `DocumentContentExtractor`, through the existing `ReferenceExtractionPort`, `dataclasses.replace`), keeping `ParagraphContentAdapter` free of reference parsing. Update `openspec/specs/extract-content/spec.md` (the "`references` MUST always be `[]`" requirement belongs to the adapter and must not block the domain service). Alternatives considered: change the classifier signature to receive the references separately; replace the DTO in the use case (rejected: the use case must stay a thin orchestrator).
- **Open verification requested by the user**: compare, on the sample documents, the references found by the legacy `ReferenceParser` in `main` with those found by `DocxReferenceAdapter` (the algorithm for the signals is already confirmed identical; the extraction parity is not).
- **Decision (2026-10-01)**: the user chose NOT to fix it now; verify against `main` first.

### F-02 (HIGH, FIXED in PR #55) Model reasoning mode consumed the token budget and left responses empty
- **Symptom**: `argumentacion = 7.0 / "No disponible"` and a `conclusiones` feedback equal to the model's internal reasoning (`Role: Expert Academic Editorial Reviewer...`); the overall score included the invented default.
- **Evidence** (`logs/ollama.log`, `ai_interactions`): with reasoning on, calls capped at `num_predict=300` (classification, editorial suitability) generated exactly 299 tokens, `done_reason=length`, empty `response`, reasoning in the separate `thinking` field; the uncapped quality call reasoned for 14 minutes (8,977 tokens, 11,071 total) without finishing; another quality call hit the 4,096-token context limit (`truncated = 1`).
- **Root cause**: the adapter did not control the `think` option.
- **Fix**: `OLLAMA_THINK` (default `false`, strict `true`/`false`) read by `EnvConfig`, injected through the wiring into `OllamaGeneratorAdapter(model_name, base_url, think)`.
- **Measured result** (same document, default 4,096 context, `think=false`): classification 14-15 tokens, quality 427-522 tokens, suitability 96-146 tokens; largest call 2,616 tokens; no truncation; whole analysis 95 s with a warm model (346 s including a cold model load) versus 526-702 s before.
- **Sizing note**: with reasoning off no `num_ctx` is needed (prompts are 1,942-2,351 tokens). With reasoning on, no context size is enough. OpenArma ran this model at 32,768 context with `think=False`; that is not required here.

### F-03 (MEDIUM, FIXED in PR #54) The web page showed nothing when an analysis failed
- htmx 1.x does not swap 4xx/5xx responses; the server returned the rendered error fragment with HTTP 400 and the page looked stuck. Fixed with a `htmx:beforeSwap` listener that paints HTML error responses only. Verified in a real headless Chrome.

### F-04 (MEDIUM, OPEN) The error message hides the real cause of a language-model failure
- Every `ollama.ResponseError`, `RequestError` and `ConnectionError` is mapped to `LanguageModelUnavailable` ("The language model backend is unavailable"). A real model-load failure (`llama-server startup failed ... out-of-memory ... status code 500`) looked identical to "Ollama is not running". The cause was recoverable only from the audit database (cause chain) and the Ollama log.
- **Proposed action**: distinct domain errors/messages for "unreachable", "model could not be loaded" and "model not found", without leaking internals to the user; keep the detail in the log.

### F-05 (MEDIUM, OPEN) Reports and audit rows carry the temporary upload name instead of the original file name
- The report JSON `filename` and the metrics `analyses.document_name` hold the random temporary name (`tmp0hog1vwr.docx`); only the report file name is derived from the original.
- **Proposed action**: carry the original file name from the upload endpoint to the use case/report DTO.

### F-06 (MEDIUM, OPEN) Two analyses of the same document overwrite each other's reports
- Both write `<name>_analisis.docx` and `<name>_analisis.json`; the last to finish wins (observed 2026-10-01 19:34). Concurrent writes could interleave.
- **Proposed action**: unique report names or one folder per analysis id.

### F-07 (MEDIUM, OPEN) A client reload or disconnect does not cancel the running analysis
- Reloading the page while an analysis ran left an orphan analysis (11.7 min) competing with the next one on a single-slot Ollama (`OLLAMA_NUM_PARALLEL=1`): a call that takes 22 s alone took 150 s.
- **Proposed action**: stop work when the client disconnects (`request.is_disconnected()` between stages), and/or a single-flight lock or queue, and/or disable the submit button while a request is in flight.

### F-08 (LOW, OPEN) Token usage and truncation are not recorded in the audit
- Ollama's `/api/generate` reply carries `prompt_eval_count`, `eval_count` and `done_reason` (`length` when output was cut). Today `LlmGeneratorPort.generate` returns only text, so an empty or cut response is a silent failure that had to be discovered from `ollama.log`.
- **Proposed action**: extend the port/DTO (or add a side channel) to record the three values and log a warning when `done_reason == "length"`. Prompt size is currently stored only in characters (`input_payload` length, or `chars=N` in PROD).

### F-09 (LOW, OPEN) Report presentation details
- The editorial-alignment "Justificacion" ends with an ellipsis: the report truncates it (the stored model answer is complete, 622 characters).
- `Confianza: -` is printed when the confidence is `None` (a consequence of F-01 for `POPULAR_SCIENCE`).
- The report footer says `v0.95` while the web footer is hardcoded `v0.8`.

### F-10 (LOW, OPEN) Pre-existing type-checker finding
- `TextIO.reconfigure` in `main.py` (lines 18-21) and `conftest.py`: the `hasattr(stdout, "reconfigure")` blocks are flagged by the type checker every time those files are touched. Left untouched on purpose in the delivered work.

### F-11 (LOW, OPEN) JVM crash dumps land in the repository root
- Under memory pressure the LanguageTool JVM crashed ("insufficient memory ... out of physical RAM or swap") and wrote `hs_err_pid*.log` and `replay_pid*.log` in the working directory; a test run showed an intermittent `GrammarCheckUnavailable`. **Proposed action**: add both patterns to `.gitignore` and consider where LanguageTool runs from.

### F-12 (OPERATIONAL, DONE) Stopping Ollama by killing only `ollama.exe` leaves GPU-holding orphans
- The `llama-server.exe` children survived three times and retained 15.1 of 16 GB of VRAM; the next load failed with `cudaMalloc failed: out of memory` (see F-04). Correct procedure: terminate the whole process tree and verify that no `llama-server.exe` remains and that VRAM dropped. Recorded in the project memory (#2508).

### F-13 (HIGH, FIXED in this branch) The Word report crashed whenever the classification had a confidence value
- **Symptom** (found by the full end-to-end run after the F-01 fix): `Error al guardar reporte Word:` (empty message), CLI exit code 1, JSON written but no `.docx`. Log: `ValueError: Unknown format code '%' for object of type 'str'` at `docx_report_adapter.py:311` (`f"{classification.confidence:.1%}"`).
- **Root cause**: `ClassificationConfidence(float, Enum)` loses its numeric `format()` on Python 3.12+ (the venv runs 3.14): `Enum.__format__` falls back to `str(member)`. Three production sites format it with `:.1%` (Word report, `ClassificationResultDTO.__str__`, `ConfidenceRule`).
- **Why it was hidden**: before F-01 was fixed the confidence was almost always `None`; only the IMRyD override path carried a value. Populating the references made it the normal case for every scientific article.
- **Fix**: `ClassificationConfidence.__format__` delegates to the float value (one place, consumers untouched), with enum, DTO and real Word-export regression tests.

### Unexplained observation
- `GET /` took 6.3 s while an analysis was running (2026-10-01 19:23:51); the logs do not explain it.

---

## 3. Scope & Constraints

### In Scope
- Record the findings, their evidence and proposed actions (this document).
- Verify in `main` how S2a/S2b were calculated (done for the algorithm and for where the references came from; pending for the extraction parity).

### Out of Scope (until the user decides per task)
- Any change to classification behavior (F-01), error messages (F-04), report naming (F-05, F-06), request cancellation (F-07) or the audit port (F-08).
- Breaking existing public interfaces without an explicit decision.

---

## 4. Checklist of Actionable Tasks

- [x] **TASK-01: Show server error responses in the htmx results area** (F-03)
  - **Outcome**: PR #54 merged (`cc83789`).

- [x] **TASK-02: Make the model reasoning mode configurable and disabled by default** (F-02)
  - **Outcome**: PR #55 merged (`4d638ff`); `OLLAMA_THINK` documented in the spec and `.env.example`.

- [x] **TASK-03: Verify S2a/S2b extraction parity against `main`** (F-01, requested by the user)
  - **Route**: direct inline (read-only investigation)
  - **Scope**: run the legacy `ReferenceParser.parse_from_docx` (from `main`, in a scratch worktree) and `DocxReferenceAdapter` over the sample documents in `silvina-doc/Archivos de prueba/`; compare counts and recency per document; record differences.
  - **Outcome (2026-10-02)**: S2a and S2b are identical for legacy and current extraction on all 10 documents; see the comparison table in section 5. The current extractor never finds fewer references than the legacy one, so the pitfall "fewer references, signals still fail" does not materialize.
  - **Verification**: comparison table in the progress log.

- [x] **TASK-04: Populate `DocumentContentDTO.references` for the classifier** (F-01)
  - **Route**: subagent delegation (`gentle-ai-worker`), own branch and PR
  - **Scope**: see F-01 proposed action; update `openspec/specs/extract-content/spec.md`; add a regression test with a real `.docx` that has references (S2a and S2b true, category `SCIENTIFIC`); evaluate the effect on structure validation and recommendations for the sample documents and document any behavior change.
  - **Verification**: full repository suite; before/after classification of every sample document.
  - **Outcome (2026-10-02, implemented, commit `0d0df1d`)**: `DocumentContentExtractor` now receives `ReferenceExtractionPort` and fills `references` with `dataclasses.replace` before the count refinement, so both the accurate-count and the fallback paths carry them; wiring updated; `extract-content` spec updated; unit tests plus a real-fixture regression test (34 references, S2a and S2b true, `SCIENTIFIC` with a stubbed `S4/S5/S6: SI` answer). Whole suite 951 passed, `ruff check` clean. References are now parsed twice per analysis (here and in `CitationExtractor`); both are cheap regex passes and the duplication was accepted to keep each domain service self-contained.
  - **End-to-end run (2026-10-02)**: real CLI analysis of `capacidades_razonamiento_emergente_LLMs.docx` (145 s, model already warm): `SCIENTIFIC`, `Confianza: 90.0%`, reasoning cites S2a and S2b; Word and JSON reports saved. The first attempt failed in the Word export, which uncovered F-13 (fixed). Added the smoke test `tests/smoke/test_extract_content_references_parity.py` (3 sample documents: 34, 11 and 4 references; S2a/S2b true only for the scientific one); verified to fail when the reference population is removed. Whole suite 960 passed, `ruff check` clean.
  - **Real-model before/after (2026-10-02)**: classification only (one real Ollama call per document, same model answer for both sides; "before" = `references=[]`, "after" = the extractor output), `gemma4-26b-adapted`, `think=false`:

    | Document | Refs | S2a | S2b | Before | After | Effective structure type |
    | --- | --- | --- | --- | --- | --- | --- |
    | Test_1 / 1. test_Cientifico | 34 | T | T | POPULAR_SCIENCE, no confidence | SCIENTIFIC, FULL_SIGNAL_MATCH | POPULAR_SCIENCE (unchanged) |
    | Test_1 / 2. test_divulgacion_v2 | 11 | F | F | POPULAR_SCIENCE | POPULAR_SCIENCE | unchanged |
    | Test_1 / 3. test_opinion_v2 | 4 | F | F | OPINION | OPINION | unchanged |
    | Test_2 / test_1_cientifico_095 | 17 | T | T | POPULAR_SCIENCE, no confidence | SCIENTIFIC, FULL_SIGNAL_MATCH | POPULAR_SCIENCE (unchanged) |
    | Test_2 / test_2_cientifico_090 | 16 | T | T | POPULAR_SCIENCE, no confidence | SCIENTIFIC, FULL_SIGNAL_MATCH | POPULAR_SCIENCE (unchanged) |
    | Test_2 / test_3_cientifico_083 | 14 | T | F | POPULAR_SCIENCE, no confidence | SCIENTIFIC, SUFFICIENT_REFERENCE_COUNT | POPULAR_SCIENCE (unchanged) |
    | Test_2 / test_4_divulgacion_caso9 | 10 | F | F | POPULAR_SCIENCE | POPULAR_SCIENCE | unchanged |
    | Test_2 / test_5_divulgacion_caso16 | 7 | F | F | POPULAR_SCIENCE | POPULAR_SCIENCE | unchanged |
    | Test_2 / test_6_opinion_caso19 | 4 | F | F | OPINION | OPINION | unchanged |
    | capacidades_razonamiento_emergente_LLMs | 34 | T | T | POPULAR_SCIENCE, no confidence | SCIENTIFIC, FULL_SIGNAL_MATCH | POPULAR_SCIENCE (unchanged) |

    Reading: the 5 scientific samples are now classified correctly (they were all `POPULAR_SCIENCE`); the 5 divulgacion/opinion samples are unchanged, so there are no false positives. `ClassificationResultDTO.effective_structure_type` keeps a `SCIENTIFIC` article that lacks IMRyD wording in its reasoning validated as `POPULAR_SCIENCE` (legacy behavior, covered by existing tests), so structure validation does not change for any sample; the recommendation code does not read the article type. The visible change is the category, confidence and reasoning shown in the report. Whether a `SCIENTIFIC` article without IMRyD should be validated as scientific is a separate product question, not part of this fix.

- [ ] **TASK-05: Specific language-model error messages** (F-04) and **TASK-07: Cancel or serialize analyses** (F-07)
  - **Route**: one branch and PR each; scopes as in the findings.

- [ ] **TASK-06: Original file name and unique report names** (F-05, F-06)
  - **Route**: subagent delegation (`gentle-ai-worker`), branch `fix/report-original-filename-and-unique-names`, own PR
  - **Design**: `AnalyzeDocumentUseCase.execute` gets an optional `document_name` (defaults to `document_path`, so the CLI is unchanged) used for the tracked analysis name and `ReportInputDTO.filename`; the upload endpoint passes the original upload name. Each web analysis writes its reports into its own sub-folder of the reports directory (`<reports_dir>/<unique id>/<name>_analisis.docx|json`), keeping the original-based file names, and the download links point to `/reports/<unique id>/<file>` (the download route already accepts sub-paths with traversal protection).
  - **Scope**: `src/application/analyze_document_use_case.py`, `src/infrastructure/fastapi/src/routes/analyze_endpoint.py`, their tests, `openspec/specs` where the report name or the upload flow is described.
  - **Verification**: failing tests first (use case records the original name in metrics start/completion and report filename; endpoint passes the original name, two analyses of the same name write to different paths, links include the folder); whole suite and `ruff check`; real web run with two uploads of the same document.
  - **Outcome (2026-10-02, implemented, uncommitted)**: `execute(document_path, document_name=None)` falls back to `document_path`; the endpoint passes the upload name and writes into `<reports_dir>/<uuid4 hex>/`; links are `/reports/<uuid>/<name>_analisis.*`; the download header still carries the bare file name. Also updated `tests/e2e/test_fastapi_e2e.py` (it asserted the flat paths) and the `analyze-document` spec. Whole suite 964 passed, `ruff check` and `ruff format --check` clean. Native review (`review-reliability`, medium risk): approved and acknowledged. Committed on branch `fix/report-original-filename-and-unique-names`. **Pending**: real web run with two uploads of the same document.

- [ ] **TASK-08: Record tokens and `done_reason` in the audit** (F-08)
  - **Scope**: extend `LlmGeneratorPort` or the Ollama adapter contract, `AiInteractionDTO`, the SQLite schema and a warning log; keep the privacy policy (`APP_MODE`).

- [ ] **TASK-09: Housekeeping** (F-09, F-10, F-11): report footer version and truncation, the type-checker finding, `.gitignore` for JVM dumps.

---

## 5. Progress & Verification Log

- **Current Status**: findings documented (2026-10-01). TASK-01 and TASK-02 delivered. User decisions so far: do not fix F-01 yet; verify the S2a/S2b behavior in `main` first; this document is the single record.
- **Next Step**: the user decides which of TASK-05 to TASK-09 to schedule; TASK-03 and TASK-04 are delivered (commit `0d0df1d` on `fix/classifier-references-s2a-s2b`).

### Verification History
- **2026-10-01, real runs** (metrics database, `silvina.log`, `ollama.log`): reasoning on vs off, 4,096 vs 32,768 context, two concurrent analyses, Ollama unreachable, Ollama model-load failure; full measurements in F-02.
- **2026-10-02, TASK-03 extraction parity** (legacy `ReferenceParser.parse_from_docx` at `main` 0c9631b vs current `DocxReferenceAdapter`, same documents; recency = share of references whose latest year is >= current year - 4):

  | Document | Legacy refs | Current refs | Legacy recency | Current recency | S2a legacy / current | Identical lists |
  | --- | --- | --- | --- | --- | --- | --- |
  | Test_1 / 1. test_Cientifico | 33 | 34 | 0.67 | 0.65 | True / True | no |
  | Test_1 / 2. test_divulgacion_v2 | 10 | 11 | 0.00 | 0.00 | False / False | no |
  | Test_1 / 3. test_opinion_v2 | 3 | 4 | 0.00 | 0.00 | False / False | no |
  | Test_2 / test_1_cientifico_095 | 17 | 17 | 0.53 | 0.53 | True / True | yes |
  | Test_2 / test_2_cientifico_090 | 16 | 16 | 0.62 | 0.62 | True / True | yes |
  | Test_2 / test_3_cientifico_083 | 14 | 14 | 0.00 | 0.00 | True / True | yes |
  | Test_2 / test_4_divulgacion_caso9 | 10 | 10 | 0.00 | 0.00 | False / False | yes |
  | Test_2 / test_5_divulgacion_caso16 | 6 | 7 | 0.17 | 0.14 | False / False | no |
  | Test_2 / test_6_opinion_caso19 | 3 | 4 | 0.00 | 0.00 | False / False | no |
  | capacidades_razonamiento_emergente_LLMs | 33 | 34 | 0.67 | 0.65 | True / True | no |

  Cause of the +1: the legacy parser discards any reference of 30 characters or fewer (`len(current_ref) > 30`), which drops a short leading entry such as `Anderson, P. W. (1972).`; the current adapter keeps it (34 is the real count of the test document). Both parsers share the same splitting artifact (a title tail can become its own item). No threshold (>= 12 references, >= 50 % recent) is crossed differently by any document.
- **2026-10-01, S2a/S2b**: algorithm in `main` confirmed identical to the current one; in `main` the references reached the classifier through `ContentExtractor.extract_content(paragraphs, docx_path)` (step 5, `ReferenceParser`); in the hexagonal code they never do (`paragraph_content_adapter.py:39`); offline reproduction flips the category from `POPULAR_SCIENCE` to `SCIENTIFIC` when the 34 references are supplied.
