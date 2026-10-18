from jinja2 import Environment

from src.domain.dtos.prompt_source_dto import PromptSourceDTO
from src.domain.dtos.report_input_dto import ReportInputDTO
from src.domain.report.report_export_port import ReportExportPort

STANDALONE_REPORT_TEMPLATE_NAME = "standalone_report.html"


class HtmlReportAdapter(ReportExportPort):
    """Export analysis reports as a standalone HTML page that works offline."""

    def __init__(
        self,
        template_environment: Environment,
        stylesheet_text: str,
        logo_data_uri: str | None,
        app_name: str,
        app_version: str,
        prompt_source: PromptSourceDTO | None = None,
    ) -> None:
        self._template_environment = template_environment
        self._stylesheet_text = stylesheet_text
        self._logo_data_uri = logo_data_uri
        self._app_name = app_name
        self._app_version = app_version
        self._prompt_source = prompt_source

    def export(self, report_input: ReportInputDTO, output_path: str) -> bool:
        """Render the report as a standalone HTML page and write it as UTF-8 to the given path."""
        template = self._template_environment.get_template(STANDALONE_REPORT_TEMPLATE_NAME)
        html = template.render(
            report=report_input,
            stylesheet_text=self._stylesheet_text,
            logo_data_uri=self._logo_data_uri,
            app_name=self._app_name,
            app_version=self._app_version,
            prompt_source_text=self._prompt_source_text(),
        )

        with open(output_path, "w", encoding="utf-8") as file:
            file.write(html)

        return True

    def _prompt_source_text(self) -> str | None:
        if self._prompt_source is None:
            return None
        return self._prompt_source.describe()
