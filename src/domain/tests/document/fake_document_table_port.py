from src.domain.document.document_table_port import DocumentTablePort
from src.domain.dtos.document_table_dto import DocumentTableDTO


class FakeDocumentTablePort(DocumentTablePort):
    def __init__(
        self,
        tables: list[DocumentTableDTO] | None = None,
        error: Exception | None = None,
    ) -> None:
        self._tables = tables if tables is not None else []
        self._error = error
        self.read_paths: list[str] = []

    def read_tables(self, path: str) -> list[DocumentTableDTO]:
        self.read_paths.append(path)
        if self._error is not None:
            raise self._error
        return self._tables
