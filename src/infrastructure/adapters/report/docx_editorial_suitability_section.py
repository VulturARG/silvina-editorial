from docx.document import Document as DocxDocument

from src.domain.dtos.report_input_dto import ReportInputDTO
from src.infrastructure.adapters.report.docx_labeled_paragraph_writer import (
    DocxLabeledParagraphWriter,
)
from src.infrastructure.adapters.report.docx_report_section import DocxReportSection
from src.infrastructure.adapters.report.docx_section_heading_writer import (
    DocxSectionHeadingWriter,
)


class DocxEditorialSuitabilitySection(DocxReportSection):
    """Render the editorial contribution and research-line alignment evaluation."""

    def __init__(
        self,
        section_heading_writer: DocxSectionHeadingWriter,
        labeled_paragraph_writer: DocxLabeledParagraphWriter,
    ) -> None:
        self._section_heading_writer = section_heading_writer
        self._labeled_paragraph_writer = labeled_paragraph_writer

    def render(self, document: DocxDocument, report_input: ReportInputDTO) -> None:
        """Add contribution and alignment blocks, or nothing when suitability is absent."""
        suitability = report_input.quality.editorial_suitability
        if suitability is None:
            return

        self._section_heading_writer.write(
            document=document, text="🎯 PERTINENCIA EDITORIAL", level=1
        )

        document.add_heading("Contribución", level=3)
        self._labeled_paragraph_writer.write(
            document=document,
            label="Veredicto: ",
            value=suitability.contribution_verdict,
        )

        if suitability.contribution_phrase:
            self._labeled_paragraph_writer.write(
                document=document,
                label="Aporte identificado: ",
                value=suitability.contribution_phrase,
            )

        self._labeled_paragraph_writer.write(
            document=document,
            label="Observación: ",
            value=suitability.contribution_observation,
        )

        document.add_heading("Alineación con líneas de investigación", level=3)
        self._labeled_paragraph_writer.write(
            document=document,
            label="Veredicto: ",
            value=suitability.alignment_verdict,
        )

        self._labeled_paragraph_writer.write(
            document=document,
            label="Líneas relacionadas: ",
            value=suitability.alignment_lines,
        )

        self._labeled_paragraph_writer.write(
            document=document,
            label="Justificación: ",
            value=suitability.alignment_justification,
        )
