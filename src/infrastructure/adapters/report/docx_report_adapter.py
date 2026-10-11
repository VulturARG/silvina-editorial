from collections.abc import Sequence

from docx import Document

from src.domain.dtos.report_input_dto import ReportInputDTO
from src.domain.report.report_export_port import ReportExportPort
from src.infrastructure.adapters.report.docx_page_decoration import DocxPageDecoration
from src.infrastructure.adapters.report.docx_report_section import DocxReportSection


class DocxReportAdapter(ReportExportPort):
    """Export analysis reports to professionally formatted Word (.docx) documents."""

    def __init__(
        self,
        page_decorations: Sequence[DocxPageDecoration],
        sections: Sequence[DocxReportSection],
    ) -> None:
        self._page_decorations = tuple(page_decorations)
        self._sections = tuple(sections)

    def export(self, report_input: ReportInputDTO, output_path: str) -> bool:
        """Write the report as a .docx file at output_path and return True on success."""
        document = Document()
        for page_decoration in self._page_decorations:
            page_decoration.apply(document=document)
        for section in self._sections:
            section.render(document=document, report_input=report_input)
        document.save(output_path)
        return True
