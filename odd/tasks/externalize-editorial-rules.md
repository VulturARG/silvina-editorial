# Feature: Externalize Editorial Rules (`editorial_norms.toml`)

- **Feature Name**: `externalize-editorial-rules`
- **File Locator**: `odd/tasks/externalize-editorial-rules.md`
- **Branch**: `feat/externalize-editorial-rules` (from `silvina_editorial_v100` at `962950a`)
- **TDD Mode**: Test-first for every behavior change (RED then GREEN)
- **TDD Runner**: `export USE_EXTERNAL_LLM=false APP_MODE=PROD; .venv/Scripts/python.exe -m unittest discover -s src -t . -p "test_*.py"` and the same with `-s tests` (do NOT invoke a test module directly)
- **Commit policy**: one work-unit commit per task, on this branch. The agent STOPS before every commit and waits for the user's approval.
- **Architecture rule**: read `.agent/skills/clean-architecture/SKILL.md` before touching `src/`.

---

## 1. Objective

Editorial rules (EUMIC format, abstract and keyword limits, required sections per article type and their aliases) are hardcoded in Python. Move them to a versioned `editorial_norms.toml` read by the program, so that a person who does not program can update them without breaking code. The existing `settings.toml` holds tuning parameters, not norms, and is renamed to `analysis_settings.toml`.

## 2. Decisions

- Inclusion criterion (user decision): a value goes to configuration when a person who does not program could want to change it without breaking the code. Technical constants, regular expressions and LLM-output parsers stay in code.
- Phase 1 (this feature, user decision): editorial norms only. Phase 2 (later, separate feature): word lists (`AUTHOR_BLACKLIST`, `SECTION_HEADERS`) and report texts.
- Format: TOML read with the stdlib `tomllib` (no new dependency). The sample `vision-conjunta.yml` from the external repository is reference material only; it is not used.
- Applicable norms: the current Silvina values (12 pt, 2.5 cm, APA 7, abstract 100-300 words, keywords 3-5). The 35,000-character limit was dropped; `[article_size]` stays as it is in the tuning file.
- Names (user decision): `settings.toml` becomes `analysis_settings.toml`; the new file is `editorial_norms.toml`, both at the project root.
- Ownership rule: one rule, one owner. Tuning parameters (grammar, quality, recommendation thresholds, report, upload, article size) stay in `analysis_settings.toml`; editorial norms go only to `editorial_norms.toml`.
- Design (user decision 2026-10-12): the norms reach the classes by constructor injection from the wirings (as `StructureValidator` already receives `max_header_length`); `editorial_norms.toml` is NOT overridable by environment variables. No domain port is needed: the domain receives plain DTOs.
- Norms file layout (TASK-02 onward): TOML sections `[document_format]`, `[figures]`, `[tables]`, `[abstract]`, `[keywords]` (TASK-04 adds the section sets). Value lists are TOML arrays and become `tuple[str, ...]` in frozen DTOs.
- Stays in code by the inclusion criterion (technical, not norm): the figure and table numbering regular expressions, `ABSTRACT_PARAGRAPH_LOOKAHEAD`, `_MAX_DISPLAYED_NON_STANDARD_SIZES`, and the violation severities. `AllowedFont` stays because the report generator also uses it.
- Open (decide in TASK-03): `MIN_WORDS_FOR_ABSTRACT_CHECK = 1000` is a detector heuristic rather than a norm; leave it in code or move it to `analysis_settings.toml`.
- Not read by this feature: human-only checks (originality, ethics, peer review) are outside Silvina.
- Known inconsistencies in the current code that this feature removes by deriving messages from the norm values: `missing_abstract` says "150-250" while the constants say 100-300; `non_standard_fonts` omits Calibri; the figure message cites APA.
- Known duplicate: `ReportInputDTO._PUBLISH_THRESHOLD = 7.0` (`report_input_dto.py:15`) duplicates `publish_threshold = 7.0` in the tuning file.
- Rename blast radius (settings.toml references): `src/infrastructure/env_config.py`, `src/infrastructure/tests/test_env_config_settings_file.py`, `src/infrastructure/tests/test_settings_file_loader.py`, `README.md`, `openspec/specs/analyze-document/spec.md`. `odd/tasks/*` and `openspec/changes/archive/` are history and are not touched.

## 3. Tasks

- [x] **TASK-01: Rename `settings.toml` to `analysis_settings.toml`**
  - **Scope**: the file, `env_config.py` (`_SETTINGS_FILE_PATH`), the two test modules, `README.md`, `openspec/specs/analyze-document/spec.md`. No behavior change.
  - **Outcome**: RED observed first (test pointing at the new name: 12 `FileNotFoundError`), then GREEN after `git mv` and the reference updates. Class names such as `SettingsFileLoader` are generic and were not renamed. Verified by gentle-ai-verify: `src` 1741 OK, `tests` 51 OK, ruff clean, no bare `settings.toml` reference left outside history areas, pure rename (content unchanged), `env_config.py` diff is the path constant only. The verifier also ran an unrequested `git add -N analysis_settings.toml` (no-op, the rename was already staged). Pre-existing advisories not addressed: `env_config.py:175` unchecked `int()`/`float()` parse, markdown lint in README and spec.
  - **Native review**: not run. The host resolved consent as declined for this candidate (medium risk, 7 files, 270 changed lines); the agent did not decline it. The decline is candidate-scoped. Independent verification by gentle-ai-verify stands in its place.
  - **Commit**: `d1462fd` `refactor(config): rename settings.toml to analysis_settings.toml` (includes this task document).
- [x] **TASK-02: Loader for `editorial_norms.toml`**
  - **Scope**: domain exceptions `editorial_norms_errors.py` (`EditorialNormsError`, `EditorialNormsFileNotFound`, `EditorialNormsFileInvalid`, `EditorialNormMissing`, `EditorialNormInvalid`, same `MESSAGE` + `detail` pattern as `settings_errors.py`); frozen DTOs `DocumentFormatNormsDTO`, `CaptionNormsDTO`, `AbstractNormsDTO`, `KeywordNormsDTO`, `EditorialNormsDTO`; infrastructure `EditorialNormsTomlReader` (file to dict, fail-fast), `EditorialNormsValueResolver` (typed `read_integer`, `read_float`, `read_string_list`, errors naming section and key, no environment variable), `EditorialNormsLoader` (builds `EditorialNormsDTO`, validates ranges); `editorial_norms.toml` at the project root with the current values (margin 2.5 cm +-0.3, font 12 pt +-1, fonts Times New Roman / Arial / Calibri, unjustified ratio 0.3, figure prefixes, table prefixes, abstract keywords and 100-300 words, keyword markers and 3-5). No consumer yet.
  - **Delegation**: `gentle-ai-worker` (multi-file), then `gentle-ai-verify`.
  - **Outcome**: 15 new files (5 exceptions in one file, 5 DTOs, reader, resolver, loader, `editorial_norms.toml`, 5 test modules, 66 new tests). The writer reported RED as `ModuleNotFoundError` in 5 test modules before the production code existed. The independent verifier (not the writer's report) found: `src` 1807 OK, `tests` 51 OK, ruff check and format clean, the 14 loaded values equal the constants in `eumic_document_standards.py` and the fonts equal `AllowedFont`, no `#` comments, local imports, `environ` or `getenv` in the new production files, one class per file (the exceptions file excepted), docstrings on public classes and methods, `domain/` imports nothing from the outer layers, nothing else modified. Minor note: when `min > max` the error names the `max_*` key. Pyright is installed in the venv (1.1.414) but was not run.
  - **Native review**: 1 lens (`review-reliability`), medium risk, 16 files, 1148 changed lines; approved and acknowledged (authority burned). The `odd/tasks` edit recording the TASK-01 commit is part of this candidate.
  - **Commit**: pending approval.
- [ ] **TASK-03: EUMIC format, abstract and keywords from the norms file**
  - **Scope**: `DocxEumicAdapter`, `EumicViolationFactory`, wiring, tests; removes `eumic_document_standards.py`. Violation messages take their numbers from the norm values.
- [ ] **TASK-04: Required sections per article type and aliases from the norms file**
  - **Scope**: `RequiredSectionsProvider`, `StructureValidator` aliases, wiring, tests.
- [ ] **TASK-05: Single source for the publication threshold**
  - **Scope**: `ReportInputDTO.is_publishable` and its callers. Higher risk: `ReportInputDTO` is consumed widely; analyze the blast radius before editing.
- [ ] **TASK-06: Documentation and final verification**
  - **Scope**: `README.md`, `openspec/specs/analyze-document/spec.md`, full `src` and `tests` suites, ruff.

## 4. Open items

- Confirm the injection design and the no-environment-override decision before TASK-02.
- Decide how TASK-05 injects the threshold into `ReportInputDTO` once its callers are listed.
