from fastapi import APIRouter, Request, Response

from src.infrastructure.fastapi.src.config.dependencies import TemplatesDep

page_router = APIRouter()


@page_router.get("/")
def get_index_page(request: Request, templates: TemplatesDep) -> Response:
    """Render the main application page."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"title": "Silvina - Asistente Editorial EUMIC"},
    )
