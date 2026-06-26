from src.domain.document.content_extraction_port import ContentExtractionPort
from src.domain.dtos.document_content_dto import DocumentContentDTO


class FakeContentExtractionPort(ContentExtractionPort):
    """Test double for ContentExtractionPort with configurable return or exception."""

    def __init__(
        self,
        result: DocumentContentDTO | None = None,
        error: Exception | None = None,
    ) -> None:
        self._result = result
        self._error = error

    def extract(self, paragraphs: list[str], docx_path: str | None = None) -> DocumentContentDTO:
        """Return the configured result or raise the configured exception."""
        if self._error is not None:
            raise self._error
        if self._result is None:
            return DocumentContentDTO(word_count=0, char_count=0)
        return self._result
