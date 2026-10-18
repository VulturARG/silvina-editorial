from base64 import b64encode
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.application.export_report_use_case import ExportReportUseCase
from src.domain.dtos.prompt_source_dto import PromptSourceDTO
from src.domain.enums.quality_dimension import QualityDimension
from src.domain.report.report_export_port import ReportExportPort
from src.infrastructure.adapters.report.html_report_adapter import HtmlReportAdapter
from src.infrastructure.env_config import EnvConfig
from src.infrastructure.fastapi.src.utils.inline_bold_renderer import InlineBoldRenderer

_INFRASTRUCTURE_DIRECTORY = Path(__file__).resolve().parents[1]
_STANDALONE_TEMPLATES_DIRECTORY = _INFRASTRUCTURE_DIRECTORY / "adapters" / "report" / "templates"
_FASTAPI_TEMPLATES_DIRECTORY = _INFRASTRUCTURE_DIRECTORY / "fastapi" / "templates"
_STYLESHEET_PATH = _INFRASTRUCTURE_DIRECTORY / "fastapi" / "static" / "css" / "silvina.css"
_LOGO_PATH = _INFRASTRUCTURE_DIRECTORY / "fastapi" / "static" / "img" / "silvina_logo.png"


class HtmlReportWiring:
    """Factory for building a ready-to-use ExportReportUseCase wired to standalone HTML output."""

    def __init__(self, prompt_source: PromptSourceDTO | None = None) -> None:
        """Keep the prompt source shown in the standalone report, when given."""
        self._prompt_source = prompt_source

    def create_use_case(self) -> ExportReportUseCase:
        """Return an ExportReportUseCase wired to the standalone HTML report adapter."""
        return ExportReportUseCase(report_export_port=self._report_export_port())

    def _report_export_port(self) -> ReportExportPort:
        environment_configuration = self._environment_configuration()
        return HtmlReportAdapter(
            template_environment=self._template_environment(),
            stylesheet_text=self._stylesheet_text(),
            logo_data_uri=self._logo_data_uri(),
            app_name=environment_configuration.silvina_app_name,
            app_version=environment_configuration.silvina_version,
            prompt_source=self._prompt_source,
        )

    def _environment_configuration(self) -> EnvConfig:
        return EnvConfig()

    def _template_environment(self) -> Environment:
        environment = Environment(
            loader=FileSystemLoader(
                [str(_STANDALONE_TEMPLATES_DIRECTORY), str(_FASTAPI_TEMPLATES_DIRECTORY)]
            ),
            autoescape=select_autoescape(),
        )
        environment.filters["inline_bold"] = InlineBoldRenderer().render
        environment.filters["dimension_label"] = QualityDimension.label_for
        return environment

    def _stylesheet_text(self) -> str:
        return _STYLESHEET_PATH.read_text(encoding="utf-8")

    def _logo_data_uri(self) -> str:
        encoded_logo = b64encode(_LOGO_PATH.read_bytes()).decode("ascii")
        return f"data:image/png;base64,{encoded_logo}"
