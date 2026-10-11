try:
    from docx import Document

    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

from src.domain.dtos.report_input_dto import ReportInputDTO
from src.domain.exceptions.report_errors import ReportExportUnavailable
from src.domain.report.report_export_port import ReportExportPort
from src.infrastructure.adapters.report.docx_page_decoration import DocxPageDecoration
from src.infrastructure.adapters.report.docx_report_section import DocxReportSection


class DocxReportAdapter(ReportExportPort):
    """Export analysis reports to professionally formatted Word (.docx) documents."""

    def __init__(
        self,
        base_style_decoration: DocxPageDecoration,
        header_logo_decoration: DocxPageDecoration,
        page_number_decoration: DocxPageDecoration,
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
    ) -> None:
        if not DOCX_AVAILABLE:
            raise ReportExportUnavailable()
        self._base_style_decoration = base_style_decoration
        self._header_logo_decoration = header_logo_decoration
        self._page_number_decoration = page_number_decoration
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

        self._base_style_decoration.apply(document=document)
        self._header_logo_decoration.apply(document=document)
        self._page_number_decoration.apply(document=document)
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
