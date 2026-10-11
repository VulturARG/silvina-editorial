from docx.document import Document as DocxDocument

from src.domain.dtos.report_input_dto import ReportInputDTO
from src.infrastructure.adapters.report.docx_labeled_paragraph_writer import (
    DocxLabeledParagraphWriter,
)
from src.infrastructure.adapters.report.docx_report_section import DocxReportSection
from src.infrastructure.adapters.report.docx_section_heading_writer import (
    DocxSectionHeadingWriter,
)

MISSING_CONFIDENCE_PLACEHOLDER = "—"


class DocxClassificationSection(DocxReportSection):
    """Render the article classification with its confidence and reasoning."""

    def __init__(
        self,
        section_heading_writer: DocxSectionHeadingWriter,
        labeled_paragraph_writer: DocxLabeledParagraphWriter,
    ) -> None:
        self._section_heading_writer = section_heading_writer
        self._labeled_paragraph_writer = labeled_paragraph_writer

    def render(self, document: DocxDocument, report_input: ReportInputDTO) -> None:
        """Add the article category, the confidence and the optional reasoning."""
        self._section_heading_writer.write(
            document=document, text="🏷️ CLASIFICACIÓN DEL ARTÍCULO", level=1
        )

        classification = report_input.classification

        self._labeled_paragraph_writer.write(
            document=document,
            label="Categoría: ",
            value=classification.article_type.value.upper(),
        )

        confidence_text = (
            f"{classification.confidence:.1%}"
            if classification.confidence is not None
            else MISSING_CONFIDENCE_PLACEHOLDER
        )
        self._labeled_paragraph_writer.write(
            document=document,
            label="Confianza: ",
            value=confidence_text,
        )

        if not classification.reasoning:
            return

        self._labeled_paragraph_writer.write(
            document=document,
            label="Razonamiento: ",
            value=classification.reasoning,
        )
