from pathlib import Path

from docx import Document
from docx.opc.exceptions import PackageNotFoundError

from src.domain.document.document_text_port import DocumentTextPort
from src.domain.exceptions.decorators.generic_error_handler import generic_error_handler
from src.domain.exceptions.document_errors import DocumentNotFound, DocumentUnreadable


class DocxTextAdapter(DocumentTextPort):
    """Reads raw paragraph text from a `.docx` file using python-docx."""

    @generic_error_handler
    def read_paragraphs(self, path: str) -> list[str]:
        """Return the document's non-empty stripped paragraphs, in order."""
        if not Path(path).exists():
            raise DocumentNotFound()
        try:
            document = Document(path)
        except (PackageNotFoundError, ValueError, OSError) as exc:
            raise DocumentUnreadable() from exc
        return [text for paragraph in document.paragraphs if (text := paragraph.text.strip())]
