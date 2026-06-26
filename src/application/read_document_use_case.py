from src.domain.document.document_text_port import DocumentTextPort
from src.domain.exceptions.decorators.generic_error_handler import generic_error_handler


class ReadDocumentUseCase:
    """Reads raw paragraph text from a document via a DocumentTextPort."""

    def __init__(self, port: DocumentTextPort) -> None:
        self._port = port

    @generic_error_handler
    def execute(self, path: str) -> list[str]:
        """Return the document's paragraphs, delegating to the port unchanged."""
        return self._port.read_paragraphs(path)
