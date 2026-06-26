from src.domain.document.document_text_port import DocumentTextPort


class FakeDocumentTextPort(DocumentTextPort):
    def __init__(self, paragraphs: list[str] | None = None, error: Exception | None = None) -> None:
        self._paragraphs = paragraphs if paragraphs is not None else []
        self._error = error

    def read_paragraphs(self, path: str) -> list[str]:
        if self._error is not None:
            raise self._error
        return self._paragraphs
