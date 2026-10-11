from abc import ABC, abstractmethod

from docx.document import Document as DocxDocument


class DocxPageDecoration(ABC):
    """Decorate the page furniture shared by every page of the Word analysis report."""

    @abstractmethod
    def apply(self, document: DocxDocument) -> None:
        """Apply this decoration to the document."""
