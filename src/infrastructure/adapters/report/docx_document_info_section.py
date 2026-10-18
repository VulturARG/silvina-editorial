from docx.document import Document as DocxDocument

from src.domain.dtos.prompt_source_dto import PromptSourceDTO
from src.domain.dtos.report_input_dto import ReportInputDTO
from src.infrastructure.adapters.report.docx_labeled_paragraph_writer import (
    DocxLabeledParagraphWriter,
)
from src.infrastructure.adapters.report.docx_report_section import DocxReportSection
from src.infrastructure.adapters.report.docx_report_settings import DocxReportSettings
from src.infrastructure.adapters.report.docx_section_heading_writer import (
    DocxSectionHeadingWriter,
)

UNKNOWN_AUTHORS_PLACEHOLDER = "No identificado"


class DocxDocumentInfoSection(DocxReportSection):
    """Render the analyzed document metadata and size statistics."""

    def __init__(
        self,
        docx_report_settings: DocxReportSettings,
        section_heading_writer: DocxSectionHeadingWriter,
        labeled_paragraph_writer: DocxLabeledParagraphWriter,
        prompt_source: PromptSourceDTO | None = None,
    ) -> None:
        self._docx_report_settings = docx_report_settings
        self._section_heading_writer = section_heading_writer
        self._labeled_paragraph_writer = labeled_paragraph_writer
        self._prompt_source = prompt_source

    def render(self, document: DocxDocument, report_input: ReportInputDTO) -> None:
        """Add title, authors, word and character counts and estimated pages."""
        self._section_heading_writer.write(
            document=document, text="📄 INFORMACIÓN DEL DOCUMENTO", level=1
        )

        document_content = report_input.document_content
        estimated_pages = document_content.word_count // self._docx_report_settings.words_per_page

        self._labeled_paragraph_writer.write(
            document=document,
            label="Título: ",
            value=document_content.title or report_input.filename,
        )

        self._labeled_paragraph_writer.write(
            document=document,
            label="Autor(es): ",
            value=document_content.authors or UNKNOWN_AUTHORS_PLACEHOLDER,
        )

        self._labeled_paragraph_writer.write(
            document=document,
            label="Total de palabras: ",
            value=f"{document_content.word_count:,}",
        )

        self._labeled_paragraph_writer.write(
            document=document,
            label="Total de caracteres: ",
            value=f"{document_content.char_count:,}",
        )

        self._labeled_paragraph_writer.write(
            document=document,
            label="Páginas estimadas: ",
            value=str(estimated_pages),
        )

        if self._prompt_source is not None:
            self._labeled_paragraph_writer.write(
                document=document,
                label="Prompts utilizados: ",
                value=self._prompt_source.describe(),
            )
