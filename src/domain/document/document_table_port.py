from abc import ABC, abstractmethod

from src.domain.dtos.document_table_dto import DocumentTableDTO


class DocumentTablePort(ABC):
    """Port for reading the tables of a document with their position among its paragraphs."""

    @abstractmethod
    def read_tables(self, path: str) -> list[DocumentTableDTO]:
        """Return the document's non-empty tables, in order, each with its paragraph position."""
