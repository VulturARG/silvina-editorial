from typing import cast

from docx.document import Document as DocxDocument
from docx.shared import Pt
from docx.styles.style import ParagraphStyle

from src.infrastructure.adapters.report.docx_page_decoration import DocxPageDecoration
from src.infrastructure.adapters.report.docx_report_settings import DocxReportSettings

BASE_STYLE_NAME = "Normal"
BASE_PARAGRAPH_SPACING_PT = 0


class DocxBaseStyleDecoration(DocxPageDecoration):
    """Configure the base paragraph style used by the whole report."""

    def __init__(self, docx_report_settings: DocxReportSettings) -> None:
        self._docx_report_settings = docx_report_settings

    def apply(self, document: DocxDocument) -> None:
        """Set the base style font, size, line spacing and paragraph spacing from the settings."""
        base_style = cast(ParagraphStyle, document.styles[BASE_STYLE_NAME])
        base_style.font.name = self._docx_report_settings.font_name
        base_style.font.size = Pt(self._docx_report_settings.base_font_size_pt)
        base_style.paragraph_format.line_spacing = self._docx_report_settings.line_spacing
        base_style.paragraph_format.space_after = Pt(BASE_PARAGRAPH_SPACING_PT)
        base_style.paragraph_format.space_before = Pt(BASE_PARAGRAPH_SPACING_PT)
