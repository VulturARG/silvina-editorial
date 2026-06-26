from abc import ABC, abstractmethod


class DocumentTextPort(ABC):
    """Port for reading raw paragraph text from a document."""

    @abstractmethod
    def read_paragraphs(self, path: str) -> list[str]:
        """Return the document's non-empty stripped paragraphs, in order."""
