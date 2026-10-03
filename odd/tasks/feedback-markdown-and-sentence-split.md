# Feature: Feedback Markdown Rendering and Sentence Split

- **Feature Name**: `feedback-markdown-and-sentence-split`
- **File Locator**: `odd/tasks/feedback-markdown-and-sentence-split.md`
- **Branch**: `fix/feedback-markdown-and-sentence-split` (from `feat/external-llm-debug-adapter`, which holds the parser from TASK-10)
- **TDD Mode**: Enabled (RED -> GREEN -> REFACTOR)
- **TDD Runner**: `.venv/Scripts/python -m pytest src/`
- **Delivery Strategy**: `ask-on-risk`

---

## 1. Objective

Fix two defects found in the review of the real Claude run of 2026-10-03 10:49 (analysis `544657c5…`, report `capacidades_razonamiento_emergente_LLMs_analisis (3).docx`).

## 2. Findings

- **F-1 Markdown shown raw in the web.** `QualityResponseParser` keeps paired `**` on purpose because the DOCX adapter renders them as bold (TASK-10 of `external-llm-debug-adapter`). `templates/partials/_results.html` prints `{{ feedback }}` escaped, so the browser shows literal `**Pregunta central bien definida**:`.
- **F-2 Feedback cut at "et al.".** `QualityResponseParser._extract_feedback` splits on every `"."`, so `(Wei et al., 2022; Elhage et al., 2022)` is cut in the middle (the report shows Coherencia ending in `Elhage et al.`). Happens in DOCX and web.

## 3. Scope

### In scope
- F-1: a safe inline-bold rendering for the web templates (escape first, then turn paired `**x**` into `<strong>x</strong>`), applied to every free-text field the LLM produces.
- F-2: sentence splitting in the parser that does not break on abbreviations such as `et al.`, on decimals or on initials.

### Out of scope (decided with the user, 2026-10-03)
- F-3: `analyses.article_type` stores `effective_structure_type` instead of the classification category. To be done after F-1 and F-2 are tested satisfactorily.
- Unpaired leading `**` in the editorial suitability contribution (`Aporte identificado: ** Síntesis…`): reported to the user, not decided.
- Dimension label without accent (`Argumentacion`).
- The unpaired leading `**` in `Aporte identificado` did not appear in the run of 2026-10-03 11:37 (the raw model output had no `**`), so it depends on the model format; still not decided.

## 4. Tasks

- [x] **TASK-01** (F-2, domain) Sentence splitting in `QualityResponseParser` that keeps `et al.`, decimals and initials together; keep the 3-sentence cap and the dangling `**` cleanup. Regression test built from the stored Claude response (`ai_interactions` id 39, Coherencia). New domain class `SentenceSplitter` (`split`, `cap_sentences`); the cap now slices the original text instead of re-joining. RED 3 parser failures plus the splitter module missing; `pytest src/ tests/` 1159 passed, ruff clean (re-run by the parent). Re-parsing the stored response 39: Coherencia keeps `(Wei et al., 2022; Elhage et al., 2022)` intact. Commit `a5a2293`.
- [x] **TASK-02** (F-1, infrastructure) Jinja filter for inline bold registered where the templates are built (both places in `dependencies.py`), applied in `_results.html` to feedback, contribution observation, alignment justification and recommendation messages. Tests: escaping of HTML, paired bold, unpaired `**` left as text. New class `InlineBoldRenderer` (escape first, then `**x**` to `<strong>`, one line at most); `_create_templates` helper in `dependencies.py` removes the duplicated setup. RED 12 failing first; `pytest src/ tests/` 1170 passed, ruff clean (re-run by the parent). Checked by hand on the registered filter: `<b>` and quotes escaped, pairs become `<strong>`, a lone `**` stays text. Commit `3b752bb`.
- [x] **TASK-03** Real check: run the web analysis with `USE_EXTERNAL_LLM=true`, verify the rendered page and the DOCX; user confirms. Done 2026-10-03 11:37 (analysis `02d5cc57…`, report `analisis (4)`): the DOCX has no literal `**` and Coherencia keeps its citations; the user confirmed that the web shows the bold text correctly. Timings of that run: total 59.5 s, `analyze_quality` 47.98 s (four sequential Claude calls), no errors in `silvina.log`.
- [ ] **TASK-04** (deferred by the user, 2026-10-03, F-4) Cap at 3 sentences cuts at list numbers: Argumentación ends in `…pronunciada). 3.` and Conclusiones in `…**Debilidades conclusivas:** 1.`; `---` and `> ` markers also leak (reproduced by re-parsing `ai_interactions` id 44 and 45). Not started: the user has not decided when.
- [ ] **TASK-05** (deferred by the user, 2026-10-03, F-5) Layout of the LLM feedback, in the web and in the DOCX: bold elements that are headings (`Debilidades`, `Debilidades menores`, `Notas`, `Fortalezas:`…) must start on a new line, and so must enumerations (`1.`, `2.`, or similar). The design must tell a heading apart from a bold phrase that is only emphasis inside a sentence (for example `**argumentación sólida y bien jerarquizada**`); the rule to tell them apart is NOT decided yet. Touches the parser, the DOCX adapter and the web filter. Not started.

## 5. Evidence

(commit identities and observed checks are recorded here per task)
- Commits (2026-10-03, at the user's order): TASK-01 `a5a2293`, TASK-02 `3b752bb`. Pre-commit hooks passed. Not pushed.
