from os import getenv
from pathlib import Path
from typing import Annotated

from fastapi import Depends
from fastapi.templating import Jinja2Templates

from src.application.analyze_document_use_case import AnalyzeDocumentUseCase
from src.application.export_report_use_case import ExportReportUseCase
from src.application.warm_up_language_model_use_case import WarmUpLanguageModelUseCase
from src.domain.enums.quality_dimension import QualityDimension
from src.domain.metrics.analysis_cancellation_port import AnalysisCancellationPort
from src.infrastructure.env_config import EnvConfig
from src.infrastructure.fastapi.src.utils.inline_bold_renderer import (
    InlineBoldRenderer,
)
from src.infrastructure.fastapi.src.utils.static_asset_url_builder import (
    StaticAssetUrlBuilder,
)
from src.infrastructure.wirings.analysis_cancellation_wiring import (
    AnalysisCancellationWiring,
)
from src.infrastructure.wirings.analyze_document_use_case_wiring import (
    AnalyzeDocumentUseCaseWiring,
)
from src.infrastructure.wirings.export_report_wiring import ExportReportWiring
from src.infrastructure.wirings.json_report_wiring import JsonReportWiring
from src.infrastructure.wirings.warm_up_language_model_use_case_wiring import (
    WarmUpLanguageModelUseCaseWiring,
)

STATIC_DIR = Path(__file__).resolve().parents[2] / "static"
TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "templates"


def _create_templates(environment_configuration: EnvConfig) -> Jinja2Templates:
    """Create and configure Jinja2Templates with global variables and filters."""
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
    templates.env.globals["app_name"] = environment_configuration.silvina_app_name
    templates.env.globals["app_version"] = environment_configuration.silvina_version
    templates.env.globals["static_url"] = StaticAssetUrlBuilder(STATIC_DIR).build
    templates.env.filters["inline_bold"] = InlineBoldRenderer().render
    templates.env.filters["dimension_label"] = QualityDimension.label_for
    return templates


_env_config: EnvConfig = EnvConfig()
_templates: Jinja2Templates = _create_templates(_env_config)

_analyze_use_case: AnalyzeDocumentUseCase | None = None
_export_use_case: ExportReportUseCase | None = None
_json_export_use_case: ExportReportUseCase | None = None
_analysis_cancellation_port: AnalysisCancellationPort | None = None
_warm_up_language_model_use_case: WarmUpLanguageModelUseCase | None = None


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
    global _analyze_use_case
    if _analyze_use_case is None:
        _analyze_use_case = AnalyzeDocumentUseCaseWiring().create_use_case()
    return _analyze_use_case


def get_export_report_use_case() -> ExportReportUseCase:
    """Return the singleton instance of ExportReportUseCase configured for DOCX."""
    global _export_use_case
    if _export_use_case is None:
        _export_use_case = ExportReportWiring().create_use_case()
    return _export_use_case


def get_json_export_report_use_case() -> ExportReportUseCase:
    """Return the singleton instance of ExportReportUseCase configured for JSON."""
    global _json_export_use_case
    if _json_export_use_case is None:
        _json_export_use_case = JsonReportWiring().create_use_case()
    return _json_export_use_case


def get_env_config() -> EnvConfig:
    """Return the singleton instance of EnvConfig."""
    return _env_config


def get_analysis_cancellation_port() -> AnalysisCancellationPort:
    """Return the singleton instance of AnalysisCancellationPort."""
    global _analysis_cancellation_port
    if _analysis_cancellation_port is None:
        _analysis_cancellation_port = AnalysisCancellationWiring().get_analysis_cancellation_port()
    return _analysis_cancellation_port


def get_warm_up_language_model_use_case() -> WarmUpLanguageModelUseCase:
    """Return the singleton instance of WarmUpLanguageModelUseCase."""
    global _warm_up_language_model_use_case
    if _warm_up_language_model_use_case is None:
        _warm_up_language_model_use_case = (
            WarmUpLanguageModelUseCaseWiring().get_warm_up_language_model_use_case()
        )
    return _warm_up_language_model_use_case


def initialize_dependencies() -> None:
    """Eagerly build and cache all singleton dependencies."""
    get_analyze_document_use_case()
    get_export_report_use_case()
    get_json_export_report_use_case()
    get_analysis_cancellation_port()
    get_warm_up_language_model_use_case()


def reset_dependencies() -> None:
    """Reset and re-instantiate dependency singletons, primarily for testing."""
    global \
        _analyze_use_case, \
        _export_use_case, \
        _json_export_use_case, \
        _env_config, \
        _templates, \
        _analysis_cancellation_port, \
        _warm_up_language_model_use_case
    _analyze_use_case = None
    _export_use_case = None
    _json_export_use_case = None
    _analysis_cancellation_port = None
    _warm_up_language_model_use_case = None
    _env_config = EnvConfig()
    _templates = _create_templates(_env_config)


AnalyzeUseCaseDep = Annotated[AnalyzeDocumentUseCase, Depends(get_analyze_document_use_case)]
ExportReportUseCaseDep = Annotated[ExportReportUseCase, Depends(get_export_report_use_case)]
JsonReportUseCaseDep = Annotated[ExportReportUseCase, Depends(get_json_export_report_use_case)]
EnvConfigDep = Annotated[EnvConfig, Depends(get_env_config)]
TemplatesDep = Annotated[Jinja2Templates, Depends(get_templates)]
ReportsDirDep = Annotated[Path, Depends(get_reports_directory)]
AnalysisCancellationPortDep = Annotated[
    AnalysisCancellationPort, Depends(get_analysis_cancellation_port)
]
