from docx.document import Document as DocxDocument
from docx.shared import RGBColor
from docx.text.paragraph import Paragraph

from src.infrastructure.adapters.report.docx_report_settings import DocxReportSettings


class DocxSectionHeadingWriter:
    """Add colored section headings to a Word document."""

    def __init__(self, docx_report_settings: DocxReportSettings) -> None:
        self._docx_report_settings = docx_report_settings

    def write(self, document: DocxDocument, text: str, level: int = 1) -> Paragraph:
        """Add a heading of specified level and apply heading color to all runs."""
        heading = document.add_heading(text, level=level)
        for run in heading.runs:
            run.font.color.rgb = RGBColor(*self._docx_report_settings.heading_color_rgb)
        return heading
