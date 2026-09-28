# Feature: Gradio to FastAPI Migration

- **Feature Name**: `gradio-to-fastapi-migration`
- **File Locator**: `odd/tasks/gradio-to-fastapi-migration.md`
- **TDD Mode**: Enabled (Strict TDD: RED -> GREEN -> REFACTOR)
- **TDD Runner**: `.venv\Scripts\python -m pytest`
- **Delivery Strategy**: `ask-on-risk`
- **Forecast Changed Lines**: ~650 lines (excluding templates/CSS assets)
- **Running Authored Lines**: 1111

---

## 1. Objective & Problem
Replace `gradio_app.py` as the driving web adapter of Silvina Editorial with a single FastAPI application (`src/infrastructure/fastapi/`) using Jinja2 templates, StaticFiles, and htmx.

Today, `launch_silvina.bat` runs `gradio_app.py`, which is constrained by Gradio's UI component model and blocks future capabilities (clean routing, auth, Docker). This migration achieves a strict 1:1 functional and visual port of the current flow:
- Upload `.docx`
- Synchronous blocking analysis (~60–90s) with an htmx visual processing indicator (`hx-indicator`)
- View rich report display (matching Gradio's layout and colors)
- Download Word (`.docx`) and JSON reports from `Path.home() / "Documents" / "Silvina" / "reports"`
- Root launcher `web_main.py` launching uvicorn on `127.0.0.1:7861` and auto-opening the browser.

## 2. Scope & Constraints

### In Scope
- Single FastAPI service under `src/infrastructure/fastapi/` (routers, dependencies, templates, static, utils).
- Synchronous `POST /analyze` keeping existing ~60-90s blocking behavior (no background tasks, no job IDs, no polling).
- HTTP upload validation: file extension check (reject non-`.docx`, preserve legacy `.doc` unreadable error behavior) and maximum size limit (`upload_max_size_bytes`).
- Error handling: map `BaseSrcError` subtypes to template partial error responses with the exact messages shown today.
- Visual fidelity: Jinja2 templates mirroring Gradio's `create_results_display` layout and color palette (`EUMIC_COLORS`).
- Root launcher `web_main.py` mirroring `servers_manager_api/main.py` pattern with browser auto-open via lifespan.
- `launch_silvina.bat` pointing to `python web_main.py`.
- Removal of `gradio_app.py` and updating `requirements.txt`.

### Out of Scope
- Authentication, authorization, multi-user sessions, CSRF.
- Asynchronous task queuing, redis/celery/background worker.
- Docker / containerization / reverse proxy.
- Changes to `AnalyzeDocumentUseCase` or `ExportReportUseCase` (consumed unmodified).
- Changes to CLI `main.py` (kept as independent CLI entry point).

---

## 3. Checklist of Actionable Tasks

- [x] **TASK-01: EnvConfig upload size configuration**
  - **Route**: direct inline
  - **Scope**: Add `upload_max_size_bytes: int = int(getenv("UPLOAD_MAX_SIZE_BYTES", "26214400"))` (25MB) to `src/infrastructure/env_config.py`.
  - **Verification**: Unit tests in `src/infrastructure/tests/test_env_config.py` (RED -> GREEN).

- [x] **TASK-02: Upload validator component**
  - **Route**: delegated direct
  - **Scope**: Create `src/infrastructure/fastapi/src/utils/upload_validator.py` with `validate_and_persist(upload: UploadFile, max_size_bytes: int) -> Path`. Validates size, extension (`.docx` allowed, `.doc` raises `DocumentUnreadable`, other extensions rejected). Writes temp file.
  - **Verification**: Unit tests in `src/infrastructure/fastapi/tests/test_upload_validator.py` and domain exception tests in `src/domain/tests/exceptions/` (RED -> GREEN).

- [x] **TASK-03: Dependency injection & Wiring**
  - **Route**: direct inline
  - **Scope**: Create `src/infrastructure/fastapi/src/config/dependencies.py` providing module singletons for `AnalyzeDocumentUseCase` and `ExportReportUseCase`.
  - **Verification**: Unit tests in `src/infrastructure/fastapi/tests/test_dependencies.py`.

- [x] **TASK-04: Jinja2 Templates & Static Assets**
  - **Route**: delegated direct
  - **Scope**: Port `gradio_app.py` UI into:
    - `src/infrastructure/fastapi/templates/base.html` (HTMX script, metadata, layout)
    - `src/infrastructure/fastapi/templates/index.html` (upload form, hx-indicator)
    - `src/infrastructure/fastapi/templates/partials/_results.html` (publication status banner, quality scores, error cards, semantic dimensions, critical issues, download buttons)
    - `src/infrastructure/fastapi/templates/partials/_error.html` (formatted error callouts matching Gradio strings)
    - `src/infrastructure/fastapi/static/css/silvina.css` & assets
  - **Verification**: Template rendering tests in `src/infrastructure/fastapi/tests/test_templates.py`.

- [x] **TASK-05: FastAPI App & Exception Handlers**
  - **Route**: delegated direct
  - **Scope**: Create `src/infrastructure/fastapi/fastapi_app.py` setting up `FastAPI`, mounting static files, configuring `Jinja2Templates`, registering exception handlers for `BaseSrcError` and subtypes, and lifespan browser open hook.
  - **Verification**: Test exception handlers with TestClient in `src/infrastructure/fastapi/tests/test_exception_handlers.py`.

- [x] **TASK-06: Routes (Page, Analyze, Report)**
  - **Route**: delegated direct
  - **Scope**:
    - `src/infrastructure/fastapi/src/routes/page_endpoint.py`: `GET /` -> renders `index.html`.
    - `src/infrastructure/fastapi/src/routes/analyze_endpoint.py`: `POST /analyze` (sync multipart upload, validate, run pipeline, return `_results.html`).
    - `src/infrastructure/fastapi/src/routes/report_endpoint.py`: `GET /reports/{filename}` -> secure `FileResponse` restricted to reports directory, path traversal protected.
  - **Verification**: Integration tests with `TestClient` in `src/infrastructure/fastapi/tests/test_routes.py`.

- [ ] **TASK-07: Root launcher `web_main.py` and `launch_silvina.bat`**
  - **Route**: direct inline
  - **Scope**: Create `web_main.py` calling `uvicorn.run(app, host="127.0.0.1", port=7861)` under `__main__`. Update `launch_silvina.bat` to run `python web_main.py`.
  - **Verification**: Test imports and launcher structure in `tests/test_web_main.py`.

- [ ] **TASK-08: E2E Verification & Gradio deprecation**
  - **Route**: delegated direct
  - **Scope**:
    - E2E test verifying full flow: `GET /` -> `POST /analyze` -> `GET /reports/{filename}`.
    - Remove `gradio_app.py` and legacy `tests/e2e/test_gradio_e2e.py`.
    - Update `requirements.txt` (remove `gradio`, ensure `fastapi`, `uvicorn`, `jinja2`, `python-multipart`).
  - **Verification**: Full test suite run (`.venv\Scripts\python -m pytest`).

---

## 4. Progress & Verification Log

- **Current Status**: In Progress (TASK-01 through TASK-06 complete)
- **Next Step**: TASK-07 (Root launcher `web_main.py` and `launch_silvina.bat`)

### Verification History
- **TASK-01**: Complete.
  - RED: `test_defaults_are_loaded_when_env_is_empty` and `test_env_var_overrides_upload_max_size_bytes` failed with `AttributeError` for missing `upload_max_size_bytes`.
  - GREEN: Added `self.upload_max_size_bytes: int = int(getenv("UPLOAD_MAX_SIZE_BYTES", "26214400"))` in `src/infrastructure/env_config.py`. All 19 tests in `test_env_config.py` passed.
  - REFACTOR: Full test suite green (639 passed, 6 subtests).
  - Commit: `5f3d161` (`feat(config): add upload_max_size_bytes to EnvConfig`).
  - RDD: unavailable (runtime `antigravity` is not an eligible immutable review runtime; RDD assessment returned `unassessable`).

- **TASK-02**: Complete (Delegated direct).
  - RED: Verified test collection failures for `DocumentInvalidType`, `DocumentTooLarge`, and `upload_validator.py`.
  - GREEN: Added `DocumentInvalidType` and `DocumentTooLarge` to `src/domain/exceptions/document_errors.py`. Implemented `validate_and_persist` in `src/infrastructure/fastapi/src/utils/upload_validator.py`. All 13 new unit tests passed (5 in validator with 11 subtests, 8 in domain exceptions).
  - REFACTOR: Full test suite green (652 passed, 17 subtests).
  - Commit: `48e7d8c` (`feat(fastapi): implement upload_validator with size and extension validation`).
  - RDD: unavailable (runtime `antigravity` is not an eligible immutable review runtime; RDD assessment returned `unassessable`).

- **TASK-03**: Complete (Delegated direct).
  - RED: `ModuleNotFoundError: No module named 'src.infrastructure.fastapi.src.config'` during pytest collection of `test_dependencies.py`.
  - GREEN: Implemented `src/infrastructure/fastapi/src/config/dependencies.py` with singleton use cases (`AnalyzeDocumentUseCase`, `ExportReportUseCase` for Docx and JSON, `EnvConfig`), factory getters, `reset_dependencies()`, and `Annotated[..., Depends(...)]` type aliases. All 6 tests in `test_dependencies.py` passed.
  - REFACTOR: Full test suite green (705 passed, 3 skipped).
  - Commit: `5896fed` (`feat(fastapi): implement dependency injection wiring for use cases and config`).
  - RDD: unavailable (runtime `antigravity` is not an eligible immutable review runtime; RDD assessment returned `unassessable`).

- **TASK-04**: Complete (Delegated direct).
  - RED: 7 `TemplateNotFound` failures running `pytest src/infrastructure/fastapi/tests/test_templates.py`.
  - GREEN: Implemented `base.html`, `index.html`, `partials/_results.html`, `partials/_error.html`, `silvina.css`, and static assets (`silvina_logo.png`, `logo.ico`). All 7 tests in `test_templates.py` passed.
  - REFACTOR: Full test suite green (712 passed, 3 skipped).
  - Commit: `425e640` (`feat(fastapi): implement Jinja2 templates and static assets matching Gradio layout`).
  - RDD: unavailable (runtime `antigravity` is not an eligible immutable review runtime; RDD assessment returned `unassessable`).

- **TASK-05**: Complete (Delegated direct).
  - RED: `ModuleNotFoundError: No module named 'src.infrastructure.fastapi.fastapi_app'` during pytest collection of `test_exception_handlers.py`.
  - GREEN: Implemented `src/infrastructure/fastapi/fastapi_app.py` with `create_app()`, `/static` mount, `lifespan` browser open hook, and domain exception handlers (`DocumentNotFound`, `SrcBaseNotFound`, `SrcBaseNotAuthorized`, `SrcBaseWarning`, `BaseSrcError`, `Exception`) returning `_error.html` partial with corresponding HTTP status codes (400, 403, 404, 500). All 7 tests in `test_exception_handlers.py` passed.
  - REFACTOR: Full test suite green (719 passed, 3 skipped).
  - Commit: `1d55430` (`feat(fastapi): implement FastAPI app factory and domain exception handlers`).
  - RDD: unavailable (runtime `antigravity` is not an eligible immutable review runtime; RDD assessment returned `unassessable`).

- **TASK-06**: Complete (Delegated direct).
  - RED: Collection failure on initial test file execution (`ImportError: cannot import name 'get_reports_directory' from 'src.infrastructure.fastapi.src.config.dependencies'`).
  - GREEN: Implemented `page_router` (`GET /`), `analyze_router` (`POST /analyze` with validation, pipeline execution, reports export, cleanup, and results rendering), and `report_router` (`GET /reports/{filename:path}` with path traversal protection using `is_relative_to`), wired into `dependencies.py` and `fastapi_app.py`. All 13 tests in `src/infrastructure/fastapi/tests/test_routes.py` passed.
  - REFACTOR: Full test suite green (732 passed, 3 skipped).
  - Commit: `57ae1c8` (`feat(fastapi): implement page, analyze, and report routes with path traversal guards`).
  - RDD: unavailable (runtime `antigravity` is not an eligible immutable review runtime; RDD assessment returned `unassessable`).
