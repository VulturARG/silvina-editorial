from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from logging import getLogger
from os import R_OK, access
from os.path import isfile

try:
    from docx import Document
    from docx.document import Document as DocxDocument
    from docx.enum.table import WD_ALIGN_VERTICAL
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Inches, Pt, RGBColor
    from docx.text.paragraph import Paragraph

    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

from src.domain.dtos.report_input_dto import ReportInputDTO
from src.domain.exceptions.report_errors import ReportExportUnavailable
from src.domain.report.report_export_port import ReportExportPort
from src.infrastructure.adapters.report.docx_report_section import DocxReportSection
from src.infrastructure.adapters.report.docx_report_settings import DocxReportSettings

logger = getLogger(__name__)


class DocxReportAdapter(ReportExportPort):
    """Export analysis reports to professionally formatted Word (.docx) documents."""

    def __init__(
        self,
        docx_report_settings: DocxReportSettings,
        clock: Callable[[], datetime],
        title_page_section: DocxReportSection,
        executive_summary_section: DocxReportSection,
        document_info_section: DocxReportSection,
        classification_section: DocxReportSection,
        quality_analysis_section: DocxReportSection,
        editorial_suitability_section: DocxReportSection,
        grammar_analysis_section: DocxReportSection,
        apa_validation_section: DocxReportSection,
        structure_validation_section: DocxReportSection,
        citations_analysis_section: DocxReportSection,
        recommendations_section: DocxReportSection,
        footer_section: DocxReportSection,
        logo_path: str | None = None,
    ) -> None:
        if not DOCX_AVAILABLE:
            raise ReportExportUnavailable()
        self._logo_path = logo_path
        self._docx_report_settings = docx_report_settings
        self._clock = clock
        self._title_page_section = title_page_section
        self._executive_summary_section = executive_summary_section
        self._document_info_section = document_info_section
        self._classification_section = classification_section
        self._quality_analysis_section = quality_analysis_section
        self._editorial_suitability_section = editorial_suitability_section
        self._grammar_analysis_section = grammar_analysis_section
        self._apa_validation_section = apa_validation_section
        self._structure_validation_section = structure_validation_section
        self._citations_analysis_section = citations_analysis_section
        self._recommendations_section = recommendations_section
        self._footer_section = footer_section

    def export(self, report_input: ReportInputDTO, output_path: str) -> bool:
        """Write the report as a .docx file at output_path and return True on success."""
        document = Document()

        style = document.styles["Normal"]
        style.font.name = self._docx_report_settings.font_name
        style.font.size = Pt(self._docx_report_settings.base_font_size_pt)
        style.paragraph_format.line_spacing = self._docx_report_settings.line_spacing
        style.paragraph_format.space_after = Pt(0)
        style.paragraph_format.space_before = Pt(0)

        self._add_header_logo(document=document)
        self._add_page_numbers(document=document)
        self._title_page_section.render(document=document, report_input=report_input)
        self._executive_summary_section.render(document=document, report_input=report_input)
        self._document_info_section.render(document=document, report_input=report_input)
        self._classification_section.render(document=document, report_input=report_input)
        self._quality_analysis_section.render(document=document, report_input=report_input)
        self._editorial_suitability_section.render(document=document, report_input=report_input)
        self._grammar_analysis_section.render(document=document, report_input=report_input)
        self._apa_validation_section.render(document=document, report_input=report_input)
        self._structure_validation_section.render(document=document, report_input=report_input)
        self._citations_analysis_section.render(document=document, report_input=report_input)
        self._recommendations_section.render(document=document, report_input=report_input)
        self._footer_section.render(document=document, report_input=report_input)

        document.save(output_path)
        return True

    def _add_header_logo(self, document: DocxDocument) -> None:
        if self._logo_path is None:
            return
        section = document.sections[0]
        header = section.header
        header.paragraphs[0].clear()

        table = header.add_table(
            rows=1,
            cols=2,
            width=Inches(self._docx_report_settings.header_table_width_inches),
        )

        left_cell = table.rows[0].cells[0]
        left_cell.width = Inches(self._docx_report_settings.header_left_cell_width_inches)
        left_cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        left_paragraph = left_cell.paragraphs[0]
        left_paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT

        app_label_run = left_paragraph.add_run(
            f"Generado por {self._docx_report_settings.app_name} v{self._docx_report_settings.app_version}\n"
        )
        app_label_run.italic = True
        app_label_run.font.size = Pt(self._docx_report_settings.metadata_font_size_pt)
        app_label_run.font.color.rgb = RGBColor(*self._docx_report_settings.neutral_color_rgb)

        date_run = left_paragraph.add_run(self._clock().strftime("%d de %B de %Y"))
        date_run.font.size = Pt(self._docx_report_settings.metadata_font_size_pt)
        date_run.font.color.rgb = RGBColor(*self._docx_report_settings.neutral_color_rgb)

        right_cell = table.rows[0].cells[1]
        right_cell.width = Inches(self._docx_report_settings.header_right_cell_width_inches)
        right_cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        right_paragraph = right_cell.paragraphs[0]
        right_paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT

        self._add_logo_picture(paragraph=right_paragraph, logo_path=self._logo_path)

        table_element = table._element
        table_properties = table_element.tblPr
        if table_properties is None:
            table_properties = OxmlElement("w:tblPr")
            table_element.insert(0, table_properties)

        table_borders = OxmlElement("w:tblBorders")
        for border_name in ["top", "left", "bottom", "right", "insideH", "insideV"]:
            border = OxmlElement(f"w:{border_name}")
            border.set(qn("w:val"), "none")
            border.set(qn("w:sz"), "0")
            border.set(qn("w:space"), "0")
            border.set(qn("w:color"), "auto")
            table_borders.append(border)
        table_properties.append(table_borders)

    def _add_logo_picture(self, paragraph: Paragraph, logo_path: str) -> None:
        if not (isfile(logo_path) and access(logo_path, R_OK)):
            logger.warning("Header logo is not readable, skipping picture: %s", logo_path)
            return
        logo_run = paragraph.add_run()
        logo_run.add_picture(logo_path, width=Inches(self._docx_report_settings.logo_width_inches))

    def _add_page_numbers(self, document: DocxDocument) -> None:
        section = document.sections[0]
        footer = section.footer
        footer.paragraphs[0].clear()

        paragraph = footer.paragraphs[0]
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

        page_number_run = paragraph.add_run()

        page_field_begin = OxmlElement("w:fldChar")
        page_field_begin.set(qn("w:fldCharType"), "begin")
        page_number_run._element.append(page_field_begin)

        page_instruction = OxmlElement("w:instrText")
        page_instruction.set(qn("xml:space"), "preserve")
        page_instruction.text = "PAGE"
        page_number_run._element.append(page_instruction)

        page_field_end = OxmlElement("w:fldChar")
        page_field_end.set(qn("w:fldCharType"), "end")
        page_number_run._element.append(page_field_end)

        separator_run = paragraph.add_run(" de ")
        separator_run.font.size = Pt(self._docx_report_settings.page_number_font_size_pt)

        total_pages_run = paragraph.add_run()

        total_pages_field_begin = OxmlElement("w:fldChar")
        total_pages_field_begin.set(qn("w:fldCharType"), "begin")
        total_pages_run._element.append(total_pages_field_begin)

        total_pages_instruction = OxmlElement("w:instrText")
        total_pages_instruction.set(qn("xml:space"), "preserve")
        total_pages_instruction.text = "NUMPAGES"
        total_pages_run._element.append(total_pages_instruction)

        total_pages_field_end = OxmlElement("w:fldChar")
        total_pages_field_end.set(qn("w:fldCharType"), "end")
        total_pages_run._element.append(total_pages_field_end)

        for text_run in paragraph.runs:
            text_run.font.size = Pt(self._docx_report_settings.page_number_font_size_pt)
            text_run.font.color.rgb = RGBColor(*self._docx_report_settings.neutral_color_rgb)
