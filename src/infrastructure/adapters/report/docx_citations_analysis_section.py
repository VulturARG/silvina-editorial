from docx.document import Document as DocxDocument

from src.domain.dtos.report_input_dto import ReportInputDTO
from src.infrastructure.adapters.report.citation_match_rate_formatter import (
    CitationMatchRateFormatter,
)
from src.infrastructure.adapters.report.docx_report_section import DocxReportSection
from src.infrastructure.adapters.report.docx_report_settings import DocxReportSettings
from src.infrastructure.adapters.report.docx_section_heading_writer import (
    DocxSectionHeadingWriter,
)

CITATIONS_TABLE_ROW_COUNT = 4
CITATIONS_TABLE_COLUMN_COUNT = 2


class DocxCitationsAnalysisSection(DocxReportSection):
    """Render the citation and reference counts with the citation match rate."""

    def __init__(
        self,
        docx_report_settings: DocxReportSettings,
        section_heading_writer: DocxSectionHeadingWriter,
        citation_match_rate_formatter: CitationMatchRateFormatter,
    ) -> None:
        self._docx_report_settings = docx_report_settings
        self._section_heading_writer = section_heading_writer
        self._citation_match_rate_formatter = citation_match_rate_formatter

    def render(self, document: DocxDocument, report_input: ReportInputDTO) -> None:
        """Add a styled table with citation totals, matches and match rate."""
        self._section_heading_writer.write(
            document=document, text="📚 ANÁLISIS DE CITAS Y REFERENCIAS", level=1
        )

        citations = report_input.citations

        table = document.add_table(
            rows=CITATIONS_TABLE_ROW_COUNT, cols=CITATIONS_TABLE_COLUMN_COUNT
        )
        table.style = self._docx_report_settings.table_style

        table.rows[0].cells[0].text = "Total de citas en texto"
        table.rows[0].cells[1].text = str(citations.total_citations)

        table.rows[1].cells[0].text = "Total de referencias bibliográficas"
        table.rows[1].cells[1].text = str(citations.total_references)

        table.rows[2].cells[0].text = "Citas con referencia"
        table.rows[2].cells[1].text = str(citations.matched_count)

        table.rows[3].cells[0].text = "Tasa de coincidencia"
        table.rows[3].cells[1].text = self._citation_match_rate_formatter.format(
            citations=citations
        )
