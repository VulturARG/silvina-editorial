"""FastAPI application factory, lifespan management, and exception handlers for Silvina Editorial."""

import logging
import os
import threading
import time
import webbrowser
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles

from src.domain.exceptions.base_src_error import (
    BaseSrcError,
    SrcBaseNotAuthorized,
    SrcBaseNotFound,
    SrcBaseWarning,
)
from src.domain.exceptions.document_errors import DocumentNotFound
from src.infrastructure.fastapi.src.config.dependencies import get_templates
from src.infrastructure.fastapi.src.middleware import RequestTimingMiddleware
from src.infrastructure.fastapi.src.routes import (
    analyze_router,
    page_router,
    report_router,
)

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).resolve().parent / "static"
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

templates = get_templates()


def _open_browser(url: str = "http://127.0.0.1:7861") -> None:
    """Wait briefly and attempt to open Chrome or system default browser."""
    time.sleep(1.5)
    chrome_path = "C:/Program Files/Google/Chrome/Application/chrome.exe"
    try:
        webbrowser.register("chrome", None, webbrowser.BackgroundBrowser(chrome_path))
        webbrowser.get("chrome").open(url)
    except Exception as exc:
        logger.debug("Failed opening with chrome, attempting default browser: %s", exc)
        try:
            webbrowser.open(url)
        except Exception as inner_exc:
            logger.warning("Could not open browser automatically: %s", inner_exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager that starts the browser on startup if enabled."""
    if getattr(app.state, "auto_open_browser", True) and not os.getenv("TESTING"):
        threading.Thread(target=_open_browser, daemon=True).start()
    yield


def register_exception_handlers(app: FastAPI) -> None:
    """Register domain and generic exception handlers rendering HTML error partials."""

    @app.exception_handler(DocumentNotFound)
    @app.exception_handler(SrcBaseNotFound)
    async def not_found_handler(request: Request, exc: BaseSrcError) -> Response:
        error_message = f"❌ Error de validación: {exc.dict().get('error', str(exc))}"
        return templates.TemplateResponse(
            request=request,
            name="partials/_error.html",
            context={"error_message": error_message},
            status_code=404,
        )

    @app.exception_handler(SrcBaseNotAuthorized)
    async def not_authorized_handler(request: Request, exc: SrcBaseNotAuthorized) -> Response:
        error_message = f"❌ Error de validación: {exc.dict().get('error', str(exc))}"
        return templates.TemplateResponse(
            request=request,
            name="partials/_error.html",
            context={"error_message": error_message},
            status_code=403,
        )

    @app.exception_handler(SrcBaseWarning)
    async def warning_handler(request: Request, exc: SrcBaseWarning) -> Response:
        error_message = f"❌ Error de validación: {exc.dict().get('error', str(exc))}"
        return templates.TemplateResponse(
            request=request,
            name="partials/_error.html",
            context={"error_message": error_message},
            status_code=400,
        )

    @app.exception_handler(BaseSrcError)
    async def base_src_error_handler(request: Request, exc: BaseSrcError) -> Response:
        error_message = f"❌ Error de validación: {exc.dict().get('error', str(exc))}"
        return templates.TemplateResponse(
            request=request,
            name="partials/_error.html",
            context={"error_message": error_message},
            status_code=400,
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> Response:
        error_message = f"❌ Error al procesar el documento: {str(exc)}"
        return templates.TemplateResponse(
            request=request,
            name="partials/_error.html",
            context={"error_message": error_message},
            status_code=500,
        )


def create_app(auto_open_browser: bool = True) -> FastAPI:
    """Create and configure the FastAPI application instance."""
    app = FastAPI(title="Silvina - Asistente Editorial EUMIC", lifespan=lifespan)
    app.state.auto_open_browser = auto_open_browser

    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    register_exception_handlers(app)
    app.add_middleware(RequestTimingMiddleware)

    app.include_router(page_router)
    app.include_router(analyze_router)
    app.include_router(report_router)

    return app


app = create_app()
