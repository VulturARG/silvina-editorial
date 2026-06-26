from abc import ABC, abstractmethod

from src.domain.dtos.document_content_dto import DocumentContentDTO


class ContentExtractionPort(ABC):
    """Port for extracting structured content from document paragraphs."""

    @abstractmethod
    def extract(self, paragraphs: list[str], docx_path: str | None = None) -> DocumentContentDTO:
        """Extract structured content from a list of paragraphs."""
