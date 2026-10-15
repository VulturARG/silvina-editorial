# Feature: Quality Dimension Header Without Bold

- **Feature Name**: `quality-header-without-bold`
- **File Locator**: `odd/tasks/quality-header-without-bold.md`
- **Branch**: `fix/quality-header-without-bold` (from `silvina_editorial_v100` at `8241bcc`)
- **TDD Mode**: RED -> GREEN per task
- **TDD Runner**: `export USE_EXTERNAL_LLM=false APP_MODE=PROD; .venv/Scripts/python.exe -m unittest discover -s src -t . -p "test_*.py"`
- **Commit policy**: one work-unit commit per task on the feature branch; no push, PR or merge without the user's order

---

## 1. Problem

Haiku 4.5 sometimes answers the clarity/coherence call with unbolded numbered headings (`## 1. Claridad del argumento [Puntuación: 7/10]`, `## 2. Coherencia [Puntuación: 6/10]`). `_DIMENSION_HEADER_PATTERN` in `src/domain/quality/quality_response_parser.py` requires `**`, so the text is not split. The whole response becomes one block matched to CLARITY (first 200 chars), Coherence is never matched and `QualityResponseParser.parse` fills it with the placeholder "No disponible" / 7.0. `QualityAnalyzer._ensure_call_produced_usable_content` accepts the call because CLARITY matched, so the error is silent.

Evidence: `data/metrics.db` ai_interactions ids 739 (analysis 7d19ecc7) and 719 (analysis d19bd76b); 3 of 18 Haiku 4.5 quality calls at the time of the finding (Engram observation 2678).

## 2. Decisions

- Unbolded headings are accepted only when they carry a heading marker AND a number (`#{1,6} N. <dimension>`), so body sub-headings such as `### Conclusiones parciales` do not split a block.
- A quality call must produce BOTH of its dimensions; if either is missing, `QualityAnalyzer` raises `QualityAnalysisFailed` instead of reporting the placeholder score.

## 3. Tasks

- [x] **TASK-01: Header pattern accepts `## N. <dimension>` without bold** (`quality_response_parser.py`, tests in `test_quality_response_parser.py` including the shape of ids 739 and 719)
- [x] **TASK-02: A call missing any of its two dimensions fails** (`quality_analyzer.py`, `test_quality_analyzer.py`)
- [x] **TASK-03: Full suite, ruff, regression over stored Haiku responses**

## 4. Verification evidence

- Full suite: 2183 tests, 10 failures, all in `test_env_config`, `test_env_config_settings_file` and `test_analyze_document_use_case_wiring` defaults. They are caused by the user's uncommitted `analysis_settings.toml` / `.env.example`; the same three modules pass (158 tests) on a clean worktree of HEAD.
- ruff check and format: clean on `src/domain/quality` and `src/domain/tests/quality`.
- Regression over the 80 stored quality responses: only ids 96, 719 and 739 (Haiku) change, all gaining the Coherence match; id 739 goes from the 7.0 placeholder to the real 6.0.
- With the stricter analyzer, stored Gemma responses 3, 5 and 6 (2026-10-01, thinking text leaked into the output) would now raise `QualityAnalysisFailed` instead of silently reporting a placeholder dimension.
