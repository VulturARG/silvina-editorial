# Feature: Show unmet editorial norms (EUMIC violations) in the Word report and the web results

- **Feature Name**: `show-eumic-violations`
- **File Locator**: `odd/tasks/show-eumic-violations.md`
- **Branch**: `feat/show-eumic-violations` (from `silvina_editorial_v100`)
- **TDD Mode**: Test-first for every behavior change (RED then GREEN)
- **TDD Runner**: `export USE_EXTERNAL_LLM=false APP_MODE=PROD; .venv/Scripts/python.exe -m unittest discover -s src -t . -p "test_*.py"` and the same with `-s tests` (do NOT invoke a test module directly)
- **Commit policy**: one Conventional Commit per task on the feature branch; no push, PR or merge

---

## 1. Objective

`DocxEumicAdapter` already computes `ReportInputDTO.eumic_violations`, but no report renders them. Show the list of unmet editorial norms in the Word report and in the web results.

## 2. Decisions (agreed with the user)

- Scope: only the existing EUMIC violations (format, figures, tables, formulas, abstract and keywords). Structure and APA keep their own sections.
- Every severity (INFO, WARNING, CRITICAL) is listed with its severity visible.
- When there is at least one violation, a warning is shown above the list: "No se reciben trabajos que incumplan estas normas editoriales. Corrija los puntos indicados antes de reenviar el manuscrito." Same text in Word and web.
- No violations: a positive notice ("El documento cumple las normas editoriales EUMIC evaluadas").
- No impact on verdict, executive summary, recommendations or JSON export (golden fixture unchanged). `editorial_norms.toml` unchanged (Arial 11 pt is accepted).
- Word: new level-1 section after "VALIDACIÓN DE ESTRUCTURA (EUMIC)", wired in `export_report_wiring.py`.
- Web: new card in `partials/_results.html` after "Pertinencia Editorial" and before "Problemas Críticos".

## 3. Tasks

- [x] **TASK-01: Word section**
  - **Scope**: `DocxEumicViolationsSection` in `src/infrastructure/adapters/report/`, its wiring in `export_report_wiring.py`, tests (new section test plus any characterization/wiring test affected by the extra section).
  - **Outcome**: `DocxEumicViolationsSection` registered after the structure section. `SeverityLevel.label` added (Spanish labels; enum values unchanged, so JSON export is untouched). Section tests RED (missing module) then GREEN (12/12). Docx characterization fingerprint regenerated (92 lines added, none removed). Full suite: `src` 1859 OK, `tests` 51 OK. Commit: `feat(report): list unmet EUMIC norms in the Word report` (hash in `git log`).
- [x] **TASK-02: Web card**
  - **Scope**: `src/infrastructure/fastapi/templates/partials/_results.html`, severity styles in `src/infrastructure/fastapi/static/css/silvina.css` if needed, template tests in `src/infrastructure/fastapi/tests/`.
  - **Outcome**: Card "Normas editoriales no cumplidas" placed between "Pertinencia Editorial" and "Problemas Críticos". Compliant state uses a new `.alert-success` class (silvina.css, reuses `--success-light`/`--success-color`). Violations grouped by category in first-seen order with a severity badge (label from `SeverityLevel.label`), message and details. Template tests RED (5 new tests failing, card missing) then GREEN (22/22 in `test_templates.py`). Commit: `feat(web): list unmet EUMIC norms in the analysis results` (hash in `git log`).
