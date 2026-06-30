from src.domain.dtos.report_input_dto import ReportInputDTO
from src.domain.report.report_export_port import ReportExportPort


class FakeReportExportPort(ReportExportPort):
    """Configurable fake for ReportExportPort used in application-layer tests."""

    def __init__(
        self,
        return_value: bool = True,
        raise_error: Exception | None = None,
    ) -> None:
        self._return_value = return_value
        self._raise_error = raise_error

    def export(self, report_input: ReportInputDTO, output_path: str) -> bool:
        """Return configured value or raise configured exception."""
        if self._raise_error is not None:
            raise self._raise_error
        return self._return_value
