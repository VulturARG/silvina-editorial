from dataclasses import dataclass

from src.application.analyze_document_use_case import AnalyzeDocumentUseCase
from src.application.ensure_language_model_server_use_case import (
    EnsureLanguageModelServerUseCase,
)
from src.application.export_report_use_case import ExportReportUseCase
from src.application.release_language_model_server_use_case import (
    ReleaseLanguageModelServerUseCase,
)
from src.application.warm_up_language_model_use_case import WarmUpLanguageModelUseCase
from src.domain.dtos.prompt_source_dto import PromptSourceDTO


@dataclass(frozen=True)
class CliAnalysisServices:
    """Use cases and effective model name needed by one command line document analysis."""

    analyze_document_use_case: AnalyzeDocumentUseCase
    word_report_use_case: ExportReportUseCase
    json_report_use_case: ExportReportUseCase
    html_report_use_case: ExportReportUseCase
    ensure_language_model_server_use_case: EnsureLanguageModelServerUseCase
    release_language_model_server_use_case: ReleaseLanguageModelServerUseCase
    warm_up_language_model_use_case: WarmUpLanguageModelUseCase
    model_name: str
    uses_local_language_model: bool
    warms_up_language_model: bool
    prompt_source: PromptSourceDTO
