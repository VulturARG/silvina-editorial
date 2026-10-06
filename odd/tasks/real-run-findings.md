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
- **What the model was asked**: nothing about S2a/S2b. The only classification prompt (`../../src/infrastructure/resources/prompts/classification/s4_s5_s6_signal_prompt.txt`) asks S4, S5 and S6. For the analyzed document the model answered `S4: SI`, `S5: SI`, `S6: SI` (14 tokens, 6.5 s, well formed).
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

### F-04 (MEDIUM, FIXED in this branch) The error message hides the real cause of a language-model failure
- Every `ollama.ResponseError`, `RequestError` and `ConnectionError` is mapped to `LanguageModelUnavailable` ("The language model backend is unavailable"). A real model-load failure (`llama-server startup failed ... out-of-memory ... status code 500`) looked identical to "Ollama is not running". The cause was recoverable only from the audit database (cause chain) and the Ollama log.
- **Proposed action**: distinct domain errors/messages for "unreachable", "model could not be loaded" and "model not found", without leaking internals to the user; keep the detail in the log.

### F-05 (MEDIUM, FIXED in PR #57) Reports and audit rows carry the temporary upload name instead of the original file name
- The report JSON `filename` and the metrics `analyses.document_name` hold the random temporary name (`tmp0hog1vwr.docx`); only the report file name is derived from the original.
- **Proposed action**: carry the original file name from the upload endpoint to the use case/report DTO.

### F-06 (MEDIUM, FIXED in PR #57) Two analyses of the same document overwrite each other's reports
- Both write `<name>_analisis.docx` and `<name>_analisis.json`; the last to finish wins (observed 2026-10-01 19:34). Concurrent writes could interleave.
- **Proposed action**: unique report names or one folder per analysis id.

### F-07 (MEDIUM, FIXED in this branch) A client reload or disconnect does not cancel the running analysis
- Reloading the page while an analysis ran left an orphan analysis (11.7 min) competing with the next one on a single-slot Ollama (`OLLAMA_NUM_PARALLEL=1`): a call that takes 22 s alone took 150 s.
- **Proposed action**: stop work when the client disconnects (`request.is_disconnected()` between stages), and/or a single-flight lock or queue, and/or disable the submit button while a request is in flight.

### F-08 (LOW, OPEN) Token usage and truncation are not recorded in the audit
- Ollama's `/api/generate` reply carries `prompt_eval_count`, `eval_count` and `done_reason` (`length` when output was cut). Today `LlmGeneratorPort.generate` returns only text, so an empty or cut response is a silent failure that had to be discovered from `ollama.log`.
- **Proposed action**: extend the port/DTO (or add a side channel) to record the three values and log a warning when `done_reason == "length"`. Prompt size is currently stored only in characters (`input_payload` length, or `chars=N` in PROD).

### F-09 (LOW, FIXED in this branch; truncation and `Confianza: -` left by design) Report presentation details
- The editorial-alignment "Justificacion" ends with an ellipsis: the report truncates it (the stored model answer is complete, 622 characters).
- `Confianza: -` is printed when the confidence is `None` (a consequence of F-01 for `POPULAR_SCIENCE`).
- The report footer says `v0.95` while the web footer is hardcoded `v0.8`.

### F-10 (LOW, FIXED in this branch) Pre-existing type-checker finding
- `TextIO.reconfigure` in `main.py` (lines 18-21) and `conftest.py`: the `hasattr(stdout, "reconfigure")` blocks are flagged by the type checker every time those files are touched. Left untouched on purpose in the delivered work.

### F-11 (LOW, FIXED in this branch; only the dumps are ignored) JVM crash dumps land in the repository root
- Under memory pressure the LanguageTool JVM crashed ("insufficient memory ... out of physical RAM or swap") and wrote `hs_err_pid*.log` and `replay_pid*.log` in the working directory; a test run showed an intermittent `GrammarCheckUnavailable`. **Proposed action**: add both patterns to `.gitignore` and consider where LanguageTool runs from.

### F-12 (OPERATIONAL, DONE) Stopping Ollama by killing only `ollama.exe` leaves GPU-holding orphans
- The `llama-server.exe` children survived three times and retained 15.1 of 16 GB of VRAM; the next load failed with `cudaMalloc failed: out of memory` (see F-04). Correct procedure: terminate the whole process tree and verify that no `llama-server.exe` remains and that VRAM dropped. Recorded in the project memory (#2508).

### F-13 (HIGH, FIXED in this branch) The Word report crashed whenever the classification had a confidence value
- **Symptom** (found by the full end-to-end run after the F-01 fix): `Error al guardar reporte Word:` (empty message), CLI exit code 1, JSON written but no `.docx`. Log: `ValueError: Unknown format code '%' for object of type 'str'` at `docx_report_adapter.py:311` (`f"{classification.confidence:.1%}"`).
- **Root cause**: `ClassificationConfidence(float, Enum)` loses its numeric `format()` on Python 3.12+ (the venv runs 3.14): `Enum.__format__` falls back to `str(member)`. Three production sites format it with `:.1%` (Word report, `ClassificationResultDTO.__str__`, `ConfidenceRule`).
- **Why it was hidden**: before F-01 was fixed the confidence was almost always `None`; only the IMRyD override path carried a value. Populating the references made it the normal case for every scientific article.
- **Fix**: `ClassificationConfidence.__format__` delegates to the float value (one place, consumers untouched), with enum, DTO and real Word-export regression tests.

### F-14 (MEDIUM-HIGH, OPEN) The quality evaluation sees only the first 32 % of the text, so "Conclusiones" is scored without the conclusion
- **Symptom** (report of 2026-10-02 14:57): "Conclusiones 7.0/10. Al no existir una sección formal de 'Conclusiones'... fragmento incompleto". The source document **does** have a "Conclusion" section (paragraphs 50 to 52 of 86). Yesterday's report had the same flaw (8.0).
- **Evidence**: the stored prompt of the call (`ai_interactions` id 21, `DEBUG` mode) ends the text sample in the middle of the paper and never contains the conclusion. `QualityTextSampler` was reproduced with the real `.env` values and its 8,279-character result is contained verbatim in that prompt.
- **Root cause**: the "strategic" sample (title + 3 leading + 2 middle paragraphs + conclusion) is only **250 words** for this document because the picked leading and middle paragraphs are short title, author and heading lines (20+11+8+9+4+6 words; the conclusion adds 1+115+76). `QUALITY_MIN_SAMPLE_WORD_COUNT=400`, so `build_sample` discards it and returns `_join_to_paragraph_boundary` of all paragraphs, i.e. the first 8,000 characters of the document (32 %, up to paragraph 25). The sampler had found the conclusion and then threw it away.
- **Impact**: both quality calls (prompts of 9,222 and 9,264 characters) judge only the first third; it affects any document whose leading and middle paragraphs are short, which is common. The two editorial-suitability calls (ids 22 and 23) were not examined.
- **Proposed action**: choose the leading and middle paragraphs by content (skip headings and short lines) and/or make the fallback keep the conclusion; lowering the minimum is the weakest option. Regression test with this document.

### F-15 (MEDIUM-LOW, OPEN) A citation whose reference exists is reported as unmatched (organization author glued to the previous reference)
- **Symptom**: "1 citas no tienen referencia correspondiente: (OpenAI, 2023)", match rate 96.4 % instead of 100 %, and a spurious medium recommendation. The reference `OpenAI. (2023). GPT-4 technical report...` is in the document.
- **Evidence** (real extractors): no extracted entry starts with "OpenAI"; the reference was glued to the previous one in a single 166-character entry: `Progress measures for grokking via mechanistic interpretability. International Conference on Learning Representations. https://arxiv.org/abs/2301.05217OpenAI. (2023).` That entry is then keyed `__non_author__` by the `CitationMatcher` pattern `^\w.*\d{4}.*\d{4}` (two 4-digit numbers).
- **Root cause**: `DocxReferenceAdapter` recognizes the start of a reference by the "Surname, I." shape; organization authors ("OpenAI.") do not have it and are not recognized as a new reference.
- **Methodological note**: a first simulation on raw paragraphs gave a misleading "30 of 32 references flagged"; the pipeline matches on `ReferenceDTO`, whose text is only the author-year head (`Anderson, P. W. (1972).`). Real figure: 2 of 34.
- **Proposed action**: recognize organization-author references as the start of a new entry; regression test with this document (28 of 28 matched).

### F-16 (LOW-MEDIUM, OPEN, product decision) "Gramática y Ortografía" covers about 19 % of the text and drops spelling
- `LanguageToolAdapter` checks only the first 20 paragraphs and 5,000 characters (`_MAX_PARAGRAPHS`, `_MAX_CHARS`) of about 26,000, and discards every `misspelling` match, while the report section is titled "Gramática y Ortografía 8.5/10". The source has systematic missing accents (`Introduccion`, `Conclusion`, `Revision Sistematica`) that are never reported; the three reported errors are the same missing-`¿` rule, and its suggestion (`¿En`) is placed before "En" instead of before "cuáles".
- The `_MAX_*` values are module-level constants that predate the no-constants rule. It was not checked whether this matches the legacy behavior in `main`.
- **Decision needed**: check the whole text or keep a limit (and make it configurable), and show spelling or rename the section.

### F-17 (LOW, OPEN, product decision inherited from TASK-04) The report says CIENTÍFICO but validates the structure as popular science
- The report shows "Categoría: CIENTÍFICO" and "Estructura válida según normas EUMIC", while `analyses.article_type` stores `divulgación`: `effective_structure_type` validates a `SCIENTIFIC` article without IMRyD wording as `POPULAR_SCIENCE`. The source sections are Resumen, Introducción, Enfoques teóricos, Transiciones de fase, Conclusión and Referencias (no Método or Resultados).
- **Decision needed**: should a scientific article without IMRyD be validated as scientific?

### F-18 (LOW, OPEN) A simple expected error writes three ERROR entries and two identical tracebacks
- With Ollama stopped, the first attempt (14:53:57) wrote the tracker line plus two identical full tracebacks (`Unhandled exception` and `ERROR MESSAGE`, about 7 KB) from `@generic_error_handler`; two of the three entries carry `analysis_id=-` (known: the context is already cleared).
- **Proposed action** (optional): log expected domain errors without the full traceback, or only once.

### Unexplained observation
- `GET /` took 6.3 s while an analysis was running (2026-10-01 19:23:51); the logs do not explain it.
- The application measures about 1.2 s more per language-model call than Ollama's own server log (5 calls, about 6 s of 142 s, 2026-10-02); not investigated.

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

- [x] **TASK-05: Specific language-model error messages** (F-04)
  - **Route**: subagent delegation (`gentle-ai-worker`), branch `fix/specific-language-model-error-messages`, own PR
  - **Design**: two new domain errors under `LanguageModelError`, `LanguageModelNotFound` and `LanguageModelLoadFailed`, next to the existing `LanguageModelUnavailable` (unreachable backend). `OllamaGeneratorAdapter` maps by HTTP status: 404 to not found, 5xx to load failed, anything else (other response codes, `RequestError`, `ConnectionError`) to unavailable. The original exception stays as `__cause__`, so the technical detail (for example the out-of-memory text) remains in the audit cause chain and the log, never in the user-facing message. The web handler already renders any `BaseSrcError` message; the CLI now catches the whole `LanguageModelError` family.
  - **Outcome (2026-10-02, implemented, uncommitted)**: whole suite 983 passed, `ruff check` and `ruff format --check` clean. The classification is by status code, not by message text; a 5xx is reported as "could not be loaded or run" on purpose, since it can also be a failure while running. The worker also narrowed the `TextIO.reconfigure` check in `main.py`; that is F-10 (TASK-09) and was reverted to keep this task scoped. Real CLI runs: Ollama off prints "The language model backend is unavailable."; Ollama on with `OLLAMA_MODEL_NAME=does-not-exist-model` prints "The configured language model is not installed in the backend." and the audit row keeps `caused by ResponseError: model 'does-not-exist-model' not found (status code: 404)`. The load-failed branch is covered by unit tests only (a real out-of-memory load was not reproduced).

- [x] **TASK-07: Cancel the analysis when the client disconnects** (F-07)
  - **Route**: subagent delegation (`gentle-ai-worker`), branch `fix/cancel-or-serialize-analyses`, own PR
  - **Design**: cooperative cancellation at stage boundaries. `POST /analyze` is now `async`: a watcher task awaits `request.receive()` until `http.disconnect` (no polling interval) and asks the new `AnalysisCancellationPort` to cancel; the analysis runs in a worker thread and the `ContextVar`-backed `AnalysisCancellationAdapter` carries the same `threading.Event` across the thread boundary. `AnalysisTracker.track_stage` checks the port before each stage and raises `AnalysisCancelled` (a `SrcBaseWarning`, so `@generic_error_handler` does not log it as an error); the tracker records the analysis as the new status `cancelled` (the status column is plain text, no schema change) and logs at INFO. An LLM call already in flight is not interrupted, so cancellation takes effect at the next stage boundary. The submit button is disabled while a request is in flight (`hx-disabled-elt`, supported by htmx 1.9.12). Decided against a single-flight lock or queue: cancellation removes the cause (the orphan analysis) and a queue is extra complexity for a local single-user tool.
  - **Outcome (2026-10-02, implemented, uncommitted)**: whole suite 1014 passed, `ruff check` clean. Real run (Ollama `gemma4-26b-adapted`, scratch database, log and reports directory, real server, `curl -m` to abort the connection): control analysis `success` (154 s cold, 5 model interactions); aborted at 15 s (inside `analyze_quality`) recorded as `cancelled` after 67.7 s, the in-flight stage finished and the rest was skipped; aborted at 3 s (inside `classify_article`) recorded as `cancelled` after 5.2 s with 1 model interaction instead of 5, so the quality stage (63 s, 3 model calls) never ran; the log line `Analysis cancelled after ... ms` is INFO; cancelled analyses wrote no reports and left no temporary upload; the next normal request returned `success` (no cancellation state leaked between requests). The Starlette `TestClient` cannot disconnect mid-request, so the route test patches `Request.receive`. A first worker experiment with a bare `await request.receive()` under `TestClient` hung for 20 minutes and was killed by the parent.

- [x] **TASK-06: Original file name and unique report names** (F-05, F-06)
  - **Route**: subagent delegation (`gentle-ai-worker`), branch `fix/report-original-filename-and-unique-names`, own PR
  - **Design**: `AnalyzeDocumentUseCase.execute` gets an optional `document_name` (defaults to `document_path`, so the CLI is unchanged) used for the tracked analysis name and `ReportInputDTO.filename`; the upload endpoint passes the original upload name. Each web analysis writes its reports into its own sub-folder of the reports directory (`<reports_dir>/<unique id>/<name>_analisis.docx|json`), keeping the original-based file names, and the download links point to `/reports/<unique id>/<file>` (the download route already accepts sub-paths with traversal protection).
  - **Scope**: `src/application/analyze_document_use_case.py`, `src/infrastructure/fastapi/src/routes/analyze_endpoint.py`, their tests, `openspec/specs` where the report name or the upload flow is described.
  - **Verification**: failing tests first (use case records the original name in metrics start/completion and report filename; endpoint passes the original name, two analyses of the same name write to different paths, links include the folder); whole suite and `ruff check`; real web run with two uploads of the same document.
  - **Outcome (2026-10-02, implemented, uncommitted)**: `execute(document_path, document_name=None)` falls back to `document_path`; the endpoint passes the upload name and writes into `<reports_dir>/<uuid4 hex>/`; links are `/reports/<uuid>/<name>_analisis.*`; the download header still carries the bare file name. Also updated `tests/e2e/test_fastapi_e2e.py` (it asserted the flat paths) and the `analyze-document` spec. Whole suite 964 passed, `ruff check` and `ruff format --check` clean. Native review (`review-reliability`, medium risk): approved and acknowledged. Delivered in PR #57 (merged, merge commit `09be10c`). **Real web run (2026-10-02)**: Ollama `gemma4-26b-adapted`, scratch database, log and reports directory; the same document uploaded twice returned HTTP 200 both times (107 s cold, 31 s warm), each analysis in its own folder holding both reports; the downloads work; the JSON `filename` and `analyses.document_name` are the original name in both analyses; `/reports/../metrics.db` returns 404; no temporary upload is left behind.

- [x] **TASK-08: Record tokens and `done_reason` in the audit** (F-08)
  - **Route**: subagent delegation (`gentle-ai-worker`), branch `feat/audit-token-usage-and-done-reason`, own PR
  - **Scope**: extend `LlmGeneratorPort` or the Ollama adapter contract, `AiInteractionDTO`, the SQLite schema and a warning log; keep the privacy policy (`APP_MODE`).
  - **Design**: a new non-abstract `LlmGeneratorPort.generate_with_usage` returns the frozen `LlmGenerationDTO` (`text`, `prompt_tokens`, `completion_tokens`, `done_reason`); its default implementation wraps `generate` with `None` metadata, so existing generators and test doubles keep working, and `generate` stays as the text-only entry. `OllamaGeneratorAdapter` fills the metadata from `prompt_eval_count`, `eval_count` and `done_reason` (missing keys become `None`) and `generate` delegates to it. `AuditedLlmGeneratorAdapter` records the three new trailing optional `AiInteractionDTO` fields and logs a WARNING when `done_reason` is `length` (purpose, model and token counts only, never the payload). Token counts and `done_reason` are not content, so `APP_MODE=PROD` redaction of the prompt and the output is unchanged. `ai_interactions` gets nullable `prompt_tokens`, `completion_tokens` and `done_reason` columns, added to existing databases by an idempotent `PRAGMA table_info` + `ALTER TABLE` migration; rows recorded before the change keep `NULL`. New enum `LlmDoneReason` (`stop`, `length`); the stored value is the raw backend string.
  - **Outcome (2026-10-02, implemented, uncommitted)**: whole suite 1047 passed, `ruff check` clean, `ruff format --check` clean on the touched files. RED observed before each layer (missing enum, DTO, port method, adapter metadata, SQLite columns). **Real run (2026-10-02)**: Ollama `gemma4-26b-adapted`, scratch database created with the previous (`HEAD`) schema adapter, then opened by the new adapter twice: the three columns are added once and the second open is a no-op; a short call returned `stop` with 20 prompt and 2 completion tokens; a call capped with `num_predict=12` returned `length` with 25 and 12 tokens, logged `Language model response truncated by the token limit (purpose=quality_analysis, model=gemma4-26b-adapted, prompt_tokens=25, completion_tokens=12)` without any text, and in `PROD` mode both stored payloads stayed `[REDACTED chars=... sha256=...]` while the token columns and `done_reason` were populated. The call goes through the generator wiring only (no full document analysis); no use case reads `generate_with_usage` yet, the audit is the only consumer.

- [x] **TASK-09: Housekeeping** (F-09, F-10, F-11)
  - **Route**: subagent delegation (`gentle-ai-worker`), branch `chore/housekeeping-report-footer-typecheck-gitignore`, own PR
  - **Done**: F-10: the `hasattr(stdout, "reconfigure")` guards in `main.py` and `conftest.py` became `isinstance(<stream>, TextIOWrapper)`, so the type checker no longer flags them (pi-lens stopped reporting the finding). F-11: `hs_err_pid*.log` and `replay_pid*.log` are ignored by `.gitignore`. F-09 footer: the web footer rendered a hardcoded `v0.8`; it now renders `app_name` and `app_version` (Jinja globals fed from `EnvConfig`, i.e. `version.txt`, currently 0.95), the same source as the Word report footer.
  - **Decided to leave as is (by design, 2026-10-02, user decision)**: the editorial-alignment "Justificación" ends with an ellipsis because `EditorialSuitabilityParser` deliberately keeps the first sentence and at most 120 characters (the complete model answer stays stored); and `Confianza: -` is printed only when the category has no confidence, which after F-01 is the expected case for popular science and opinion. Not touched: the parser's module-level length constants predate the no-constants rule.
  - **Outcome (2026-10-02, implemented, uncommitted)**: whole suite 1018 passed, `ruff check` clean; the rendered footer reads `Silvina Editorial Assistant v0.95`; `git check-ignore` confirms both patterns. The LanguageTool JVM crash itself (memory pressure) was not investigated: only the dumps are ignored.

- [ ] **TASK-10: Fix the quality text sample** (F-14)
  - **Status**: proposed, not scheduled. Own branch and PR. Scope: `QualityTextSampler` and its tests; regression test with `capacidades_razonamiento_emergente_LLMs.docx` (the sample must contain the conclusion). Examine the two editorial-suitability calls first.

- [ ] **TASK-11: Recognize organization-author references** (F-15)
  - **Status**: proposed, not scheduled. Own branch and PR. Scope: `DocxReferenceAdapter` and its tests; regression test with the same document (28 of 28 citations matched).

- [ ] **TASK-12: Product decisions** (F-16, F-17) and optional log cleanup (F-18)
  - **Status**: proposed, not scheduled. F-16 and F-17 need a decision before any code; F-18 is optional.

---

## 5. Progress & Verification Log

- **Current Status**: findings documented (2026-10-01). TASK-01 and TASK-02 delivered. User decisions so far: do not fix F-01 yet; verify the S2a/S2b behavior in `main` first; this document is the single record.
- **Next Step**: TASK-01 to TASK-09 are delivered. The review of the report of 2026-10-02 added F-14 to F-18 and the proposed TASK-10 to TASK-12; the user decides which to schedule (recommended order: F-14, then F-15; F-16 and F-17 are product decisions).

### Verification History
- **2026-10-02, review of a real report** (`capacidades_razonamiento_emergente_LLMs_analisis (1).docx`, generated 14:57 by the web application) cross-checked against `silvina.log`, `data/metrics.db`, the Ollama server log and the source document. The log, the audit and the report agree (first attempt failed in 7.5 s with Ollama stopped; second analysis 142 s, 5 model calls, all `done_reason=stop`, 1,942 to 2,348 prompt tokens against a 4,096 context, model load 54 s). Working: F-01 (CIENTÍFICO, 90 %), original file name and per-analysis folder (TASK-06), token and `done_reason` columns (TASK-08), footer version. Findings F-14 to F-18 above. Full write-up in Spanish: `E:\Python\silvina-doc\revision_informe_corrida_2026-10-02.md`. Three of the first hypotheses were wrong and were discarded after reproducing with the real components (an earlier paragraph matching `conclusi`; the 8,000-character cap cutting the conclusion; 30 of 32 references flagged).
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
