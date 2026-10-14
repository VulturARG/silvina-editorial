from dataclasses import dataclass

from src.application.analyze_document_use_case import AnalyzeDocumentUseCase
from src.application.export_report_use_case import ExportReportUseCase


@dataclass(frozen=True)
class CliAnalysisServices:
    """Use cases and effective model name needed by one command line document analysis."""

    analyze_document_use_case: AnalyzeDocumentUseCase
    word_report_use_case: ExportReportUseCase
    json_report_use_case: ExportReportUseCase
    html_report_use_case: ExportReportUseCase
    model_name: str
