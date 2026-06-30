from src.domain.dtos.report_input_dto import ReportInputDTO
from src.domain.exceptions.decorators.generic_error_handler import generic_error_handler
from src.domain.report.report_export_port import ReportExportPort


class ExportReportUseCase:
    """Orchestrates the export of an analysis report to a file."""

    def __init__(self, report_export_port: ReportExportPort) -> None:
        self._report_export_port = report_export_port

    @generic_error_handler
    def execute(self, report_input: ReportInputDTO, output_path: str) -> bool:
        """Delegate report export to the injected port. Returns True on success."""
        return self._report_export_port.export(report_input=report_input, output_path=output_path)
