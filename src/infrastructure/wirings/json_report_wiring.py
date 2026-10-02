from src.application.export_report_use_case import ExportReportUseCase
from src.infrastructure.adapters.report.json_report_adapter import JsonReportAdapter


class JsonReportWiring:
    """Factory for building a ready-to-use ExportReportUseCase wired to JSON output."""

    def create_use_case(self) -> ExportReportUseCase:
        return ExportReportUseCase(report_export_port=JsonReportAdapter())
