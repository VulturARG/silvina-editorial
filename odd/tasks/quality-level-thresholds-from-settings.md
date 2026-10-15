# Feature: Quality Level Thresholds From Settings

- **Feature Name**: `quality-level-thresholds-from-settings`
- **File Locator**: `odd/tasks/quality-level-thresholds-from-settings.md`
- **Branch**: `refactor/quality-level-thresholds-from-settings`, stacked on `refactor/grammar-reads-body` (the full text refactor stack) to avoid conflicts in `env_config.py`, `analysis_settings.toml` and the wiring
- **Commit policy**: stop before every commit and wait for the user's instructions. Commits by type in this order: `docs`, then code, then `test`. The code commit includes the minimal adjustments to existing tests so the full suite passes; the test commit holds only new behavior tests, preferably in new files.

---

## 1. Objective

The four keys of `[quality_level]` in `analysis_settings.toml` (`excellent_threshold`, `good_threshold`, `acceptable_threshold`, `needs_improvement_threshold`) are read by `EnvConfig` but no production code uses them: `QualityLevel` has the thresholds fixed in the code (9.0, 7.0, 5.0, 3.0). Editing the file has no effect. Make `QualityLevel` classify with the values from the settings file and remove the constants from the code.

## 2. Decisions (user, 2026-10-15)

- Option 2 of the audit: connect the keys to the domain instead of deleting them. Consistent with the rule that the code holds no tunable constants.

## 3. Tasks

- [ ] **TASK-01: Thresholds reach `QualityLevel`**
  - `QualityLevelThresholdsDTO` (`src/domain/dtos/quality_level_thresholds_dto.py`, frozen, extends `BaseDTO`): `excellent_threshold`, `good_threshold`, `acceptable_threshold`, `needs_improvement_threshold` (floats).
  - `QualityLevel` becomes a plain enum of labels (`"Excelente"`, `"Bueno"`, `"Aceptable"`, `"Requiere mejoras"`, `"Deficiente"`, values unchanged) without `min_threshold`; `from_score(score, thresholds)` returns the first level whose threshold the score reaches (`>=`), else `POOR`.
  - `QualityAnalyzer` receives `quality_level_thresholds` and passes it to `from_score`.
  - `EnvConfig.get_quality_level_thresholds()` builds the DTO from the four existing attributes; `AnalyzeDocumentUseCaseWiring._get_quality_analyzer` passes it.
  - Existing tests adjusted minimally; new behavior tests in new files: boundaries with custom thresholds (a score that is `GOOD` under defaults becomes `EXCELLENT` under lower thresholds), `get_quality_level_thresholds` maps the settings file, the wiring builds the analyzer with the real settings thresholds.
  - Done when: the full suite passes, `ruff` is clean, no `min_threshold` remains in `src`, and the audit script finds every `[quality_level]` key used in production.
