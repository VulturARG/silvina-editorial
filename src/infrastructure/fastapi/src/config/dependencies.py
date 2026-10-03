from os import getenv
from pathlib import Path
from typing import Annotated

from fastapi import Depends
from fastapi.templating import Jinja2Templates

from src.application.analyze_document_use_case import AnalyzeDocumentUseCase
from src.application.export_report_use_case import ExportReportUseCase
from src.domain.metrics.analysis_cancellation_port import AnalysisCancellationPort
from src.infrastructure.env_config import EnvConfig
from src.infrastructure.fastapi.src.utils.inline_bold_renderer import (
    InlineBoldRenderer,
)
from src.infrastructure.wirings.analysis_cancellation_wiring import (
    AnalysisCancellationWiring,
)
from src.infrastructure.wirings.analyze_document_use_case_wiring import (
    AnalyzeDocumentUseCaseWiring,
)
from src.infrastructure.wirings.export_report_wiring import ExportReportWiring
from src.infrastructure.wirings.json_report_wiring import JsonReportWiring

TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "templates"


def _create_templates(environment_configuration: EnvConfig) -> Jinja2Templates:
    """Create and configure Jinja2Templates with global variables and filters."""
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
    templates.env.globals["app_name"] = environment_configuration.silvina_app_name
    templates.env.globals["app_version"] = environment_configuration.silvina_version
    templates.env.filters["inline_bold"] = InlineBoldRenderer().render
    return templates


_env_config: EnvConfig = EnvConfig()
_templates: Jinja2Templates = _create_templates(_env_config)

_analyze_use_case: AnalyzeDocumentUseCase = AnalyzeDocumentUseCaseWiring().create_use_case()
_export_use_case: ExportReportUseCase = ExportReportWiring().create_use_case()
_json_export_use_case: ExportReportUseCase = JsonReportWiring().create_use_case()
_analysis_cancellation_port: AnalysisCancellationPort = (
    AnalysisCancellationWiring().get_analysis_cancellation_port()
)


def get_templates() -> Jinja2Templates:
    """Return the singleton instance of Jinja2Templates."""
    return _templates


def get_reports_directory() -> Path:
    """Return the output directory for generated reports."""
    reports_dir_env = getenv("SILVINA_REPORTS_DIR")
    if reports_dir_env:
        return Path(reports_dir_env)
    return Path.home() / "Documents" / "Silvina" / "reports"


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


def get_analysis_cancellation_port() -> AnalysisCancellationPort:
    """Return the singleton instance of AnalysisCancellationPort."""
    return _analysis_cancellation_port


def reset_dependencies() -> None:
    """Reset and re-instantiate dependency singletons, primarily for testing."""
    global \
        _analyze_use_case, \
        _export_use_case, \
        _json_export_use_case, \
        _env_config, \
        _templates, \
        _analysis_cancellation_port
    _analyze_use_case = AnalyzeDocumentUseCaseWiring().create_use_case()
    _export_use_case = ExportReportWiring().create_use_case()
    _json_export_use_case = JsonReportWiring().create_use_case()
    _env_config = EnvConfig()
    _templates = _create_templates(_env_config)
    _analysis_cancellation_port = AnalysisCancellationWiring().get_analysis_cancellation_port()


AnalyzeUseCaseDep = Annotated[AnalyzeDocumentUseCase, Depends(get_analyze_document_use_case)]
ExportReportUseCaseDep = Annotated[ExportReportUseCase, Depends(get_export_report_use_case)]
JsonReportUseCaseDep = Annotated[ExportReportUseCase, Depends(get_json_export_report_use_case)]
EnvConfigDep = Annotated[EnvConfig, Depends(get_env_config)]
TemplatesDep = Annotated[Jinja2Templates, Depends(get_templates)]
ReportsDirDep = Annotated[Path, Depends(get_reports_directory)]
AnalysisCancellationPortDep = Annotated[
    AnalysisCancellationPort, Depends(get_analysis_cancellation_port)
]
