from abc import ABC, abstractmethod

from docx.document import Document as DocxDocument

from src.domain.dtos.report_input_dto import ReportInputDTO


class DocxReportSection(ABC):
    """Render one section of the Word analysis report."""

    @abstractmethod
    def render(self, document: DocxDocument, report_input: ReportInputDTO) -> None:
        """Append this section's content to the document using the report input."""
