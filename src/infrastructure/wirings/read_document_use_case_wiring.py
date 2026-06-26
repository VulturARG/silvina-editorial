from src.application.read_document_use_case import ReadDocumentUseCase
from src.domain.document.document_text_port import DocumentTextPort
from src.infrastructure.adapters.document.docx_text_adapter import DocxTextAdapter


class ReadDocumentUseCaseWiring:
    """Factory for building a ready-to-use ReadDocumentUseCase."""

    def create_use_case(self) -> ReadDocumentUseCase:
        return ReadDocumentUseCase(port=self._get_document_text_port())

    def _get_document_text_port(self) -> DocumentTextPort:
        return DocxTextAdapter()
