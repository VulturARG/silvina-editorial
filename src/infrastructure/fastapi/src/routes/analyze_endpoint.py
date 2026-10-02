from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, File, Request, Response, UploadFile

from src.infrastructure.fastapi.src.config.dependencies import (
    AnalyzeUseCaseDep,
    EnvConfigDep,
    ExportReportUseCaseDep,
    JsonReportUseCaseDep,
    ReportsDirDep,
    TemplatesDep,
)
from src.infrastructure.fastapi.src.utils.upload_validator import validate_and_persist

analyze_router = APIRouter()


@analyze_router.post("/analyze")
def analyze_document(
    request: Request,
    analyze_use_case: AnalyzeUseCaseDep,
    export_use_case: ExportReportUseCaseDep,
    json_export_use_case: JsonReportUseCaseDep,
    env_config: EnvConfigDep,
    reports_dir: ReportsDirDep,
    templates: TemplatesDep,
    file: Annotated[UploadFile | None, File()] = None,
) -> Response:
    """Validate, analyze, and export analysis reports for an uploaded document."""
    raw_filename = file.filename if file is not None and file.filename else "document"
    temp_path = validate_and_persist(file, env_config.upload_max_size_bytes)
    try:
        report = analyze_use_case.execute(
            document_path=str(temp_path),
            document_name=raw_filename,
        )
    finally:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)

    analysis_folder = uuid4().hex
    base_name = Path(raw_filename).stem
    word_filename = f"{analysis_folder}/{base_name}_analisis.docx"
    json_filename = f"{analysis_folder}/{base_name}_analisis.json"
    analysis_directory = reports_dir / analysis_folder
    word_path = analysis_directory / f"{base_name}_analisis.docx"
    json_path = analysis_directory / f"{base_name}_analisis.json"

    analysis_directory.mkdir(parents=True, exist_ok=True)
    export_use_case.execute(report_input=report, output_path=str(word_path))
    json_export_use_case.execute(report_input=report, output_path=str(json_path))

    return templates.TemplateResponse(
        request=request,
        name="partials/_results.html",
        context={
            "report": report,
            "word_filename": word_filename,
            "json_filename": json_filename,
        },
    )
