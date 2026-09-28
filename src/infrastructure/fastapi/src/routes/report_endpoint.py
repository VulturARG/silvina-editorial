from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from src.infrastructure.fastapi.src.config.dependencies import ReportsDirDep

report_router = APIRouter()


@report_router.get("/reports/{filename:path}")
def download_report(
    filename: str,
    reports_dir: ReportsDirDep,
) -> FileResponse:
    """Download a generated report by filename with path traversal protection."""
    base_dir = reports_dir.resolve()
    target_path = (base_dir / filename).resolve()

    try:
        is_safe = target_path.is_relative_to(base_dir)
    except (ValueError, RuntimeError):
        is_safe = False

    if not is_safe or not target_path.is_file():
        raise HTTPException(status_code=404, detail="Report not found")

    return FileResponse(
        path=target_path,
        filename=target_path.name,
        media_type="application/octet-stream",
    )
