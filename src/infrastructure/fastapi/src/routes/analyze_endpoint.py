from pathlib import Path
from typing import Annotated
from uuid import uuid4

from anyio import create_task_group
from anyio.to_thread import run_sync
from fastapi import APIRouter, File, Request, Response, UploadFile

from src.domain.dtos.report_input_dto import ReportInputDTO
from src.domain.exceptions.base_src_error import BaseSrcError
from src.infrastructure.fastapi.src.config.dependencies import (
    AnalysisCancellationPortDep,
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
async def analyze_document(
    request: Request,
    analyze_use_case: AnalyzeUseCaseDep,
    export_use_case: ExportReportUseCaseDep,
    json_export_use_case: JsonReportUseCaseDep,
    env_config: EnvConfigDep,
    reports_dir: ReportsDirDep,
    templates: TemplatesDep,
    cancellation_port: AnalysisCancellationPortDep,
    file: Annotated[UploadFile | None, File()] = None,
) -> Response:
    """Validate, analyze, and export analysis reports for an uploaded document."""
    raw_filename = file.filename if file is not None and file.filename else "document"
    temp_path = await run_sync(validate_and_persist, file, env_config.upload_max_size_bytes)
    cancellation_port.bind_new_cancellation_signal()
    report: ReportInputDTO | None = None
    try:
        try:

            async def watch_disconnect() -> None:
                while True:
                    message = await request.receive()
                    if message["type"] == "http.disconnect":
                        cancellation_port.request_cancellation()
                        return

            try:
                async with create_task_group() as task_group:
                    task_group.start_soon(watch_disconnect)
                    report = await run_sync(
                        lambda: analyze_use_case.execute(
                            document_path=str(temp_path),
                            document_name=raw_filename,
                        )
                    )
                    task_group.cancel_scope.cancel()
            except BaseExceptionGroup as exception_group:
                for child_exception in exception_group.exceptions:
                    if isinstance(child_exception, BaseSrcError):
                        raise child_exception from None
                if len(exception_group.exceptions) == 1:
                    raise exception_group.exceptions[0] from None
                raise
        finally:
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)
    finally:
        cancellation_port.clear_cancellation_signal()

    if report is None:
        raise RuntimeError("Analysis execution produced no report")

    analysis_folder = uuid4().hex
    base_name = Path(raw_filename).stem
    word_filename = f"{analysis_folder}/{base_name}_analisis.docx"
    json_filename = f"{analysis_folder}/{base_name}_analisis.json"
    analysis_directory = reports_dir / analysis_folder
    word_path = analysis_directory / f"{base_name}_analisis.docx"
    json_path = analysis_directory / f"{base_name}_analisis.json"

    analysis_directory.mkdir(parents=True, exist_ok=True)
    await run_sync(lambda: export_use_case.execute(report_input=report, output_path=str(word_path)))
    await run_sync(
        lambda: json_export_use_case.execute(report_input=report, output_path=str(json_path))
    )

    return templates.TemplateResponse(
        request=request,
        name="partials/_results.html",
        context={
            "report": report,
            "word_filename": word_filename,
            "json_filename": json_filename,
        },
    )
