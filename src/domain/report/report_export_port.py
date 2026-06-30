from abc import ABC, abstractmethod

from src.domain.dtos.report_input_dto import ReportInputDTO


class ReportExportPort(ABC):
    """Port for exporting analysis reports to a file format."""

    @abstractmethod
    def export(self, report_input: ReportInputDTO, output_path: str) -> bool:
        """Export the report to the given path. Returns True on success."""
