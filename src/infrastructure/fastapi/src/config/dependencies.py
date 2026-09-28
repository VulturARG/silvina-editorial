from typing import Annotated

from fastapi import Depends

from src.application.analyze_document_use_case import AnalyzeDocumentUseCase
from src.application.export_report_use_case import ExportReportUseCase
from src.infrastructure.env_config import EnvConfig
from src.infrastructure.wirings.analyze_document_use_case_wiring import (
    AnalyzeDocumentUseCaseWiring,
)
from src.infrastructure.wirings.export_report_wiring import ExportReportWiring
from src.infrastructure.wirings.json_report_wiring import JsonReportWiring

_analyze_use_case: AnalyzeDocumentUseCase = AnalyzeDocumentUseCaseWiring().create_use_case()
_export_use_case: ExportReportUseCase = ExportReportWiring().create_use_case()
_json_export_use_case: ExportReportUseCase = JsonReportWiring().create_use_case()
_env_config: EnvConfig = EnvConfig()


def get_analyze_document_use_case() -> AnalyzeDocumentUseCase:
    """Return the singleton instance of AnalyzeDocumentUseCase."""
    return _analyze_use_case


def get_export_report_use_case() -> ExportReportUseCase:
    """Return the singleton instance of ExportReportUseCase configured for DOCX."""
    return _export_use_case


def get_json_export_report_use_case() -> ExportReportUseCase:
    """Return the singleton instance of ExportReportUseCase configured for JSON."""
    return _json_export_use_case


def get_env_config() -> EnvConfig:
    """Return the singleton instance of EnvConfig."""
    return _env_config


def reset_dependencies() -> None:
    """Reset and re-instantiate dependency singletons, primarily for testing."""
    global _analyze_use_case, _export_use_case, _json_export_use_case, _env_config
    _analyze_use_case = AnalyzeDocumentUseCaseWiring().create_use_case()
    _export_use_case = ExportReportWiring().create_use_case()
    _json_export_use_case = JsonReportWiring().create_use_case()
    _env_config = EnvConfig()


AnalyzeUseCaseDep = Annotated[AnalyzeDocumentUseCase, Depends(get_analyze_document_use_case)]
ExportReportUseCaseDep = Annotated[ExportReportUseCase, Depends(get_export_report_use_case)]
JsonReportUseCaseDep = Annotated[ExportReportUseCase, Depends(get_json_export_report_use_case)]
EnvConfigDep = Annotated[EnvConfig, Depends(get_env_config)]
