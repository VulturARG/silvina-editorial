from src.application.export_report_use_case import ExportReportUseCase
from src.domain.dtos.prompt_source_dto import PromptSourceDTO
from src.infrastructure.adapters.report.json_report_adapter import JsonReportAdapter


class JsonReportWiring:
    """Factory for building a ready-to-use ExportReportUseCase wired to JSON output."""

    def __init__(self, prompt_source: PromptSourceDTO | None = None) -> None:
        """Keep the prompt source written into the JSON report, when given."""
        self._prompt_source = prompt_source

    def create_use_case(self) -> ExportReportUseCase:
        return ExportReportUseCase(
            report_export_port=JsonReportAdapter(prompt_source=self._prompt_source)
        )
