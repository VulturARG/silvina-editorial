from pathlib import Path

from docx import Document
from docx.opc.exceptions import PackageNotFoundError
from docx.table import Table, _Cell, _Row

from src.domain.document.document_table_port import DocumentTablePort
from src.domain.dtos.document_table_dto import DocumentTableDTO
from src.domain.exceptions.document_errors import DocumentNotFound, DocumentUnreadable


class DocxTableAdapter(DocumentTablePort):
    """Reads the tables of a `.docx` file using python-docx."""

    def read_tables(self, path: str) -> list[DocumentTableDTO]:
        """Return the document's non-empty tables, in order, each with its paragraph position."""
        if not Path(path).exists():
            raise DocumentNotFound()
        try:
            document = Document(path)
        except (PackageNotFoundError, ValueError, OSError) as exc:
            raise DocumentUnreadable() from exc
        return self._tables_with_positions(document)

    def _tables_with_positions(self, document) -> list[DocumentTableDTO]:
        tables = []
        paragraphs_before_table = 0
        for block in document.iter_inner_content():
            if isinstance(block, Table):
                rows = self._read_rows(block)
                if rows:
                    tables.append(DocumentTableDTO(rows=rows, position=paragraphs_before_table))
            elif block.text.strip():
                paragraphs_before_table += 1
        return tables

    def _read_rows(self, table: Table) -> tuple[tuple[str, ...], ...]:
        rows = []
        cells_of_earlier_rows: list[_Cell] = []
        for row in table.rows:
            cells_of_row = self._distinct_cells(row)
            texts = tuple(
                "" if self._is_listed(cell, cells_of_earlier_rows) else cell.text.strip()
                for cell in cells_of_row
            )
            cells_of_earlier_rows.extend(cells_of_row)
            if any(texts):
                rows.append(texts)
        return tuple(rows)

    def _distinct_cells(self, row: _Row) -> list[_Cell]:
        distinct_cells: list[_Cell] = []
        for cell in row.cells:
            if not self._is_listed(cell, distinct_cells):
                distinct_cells.append(cell)
        return distinct_cells

    def _is_listed(self, cell: _Cell, cells: list[_Cell]) -> bool:
        return any(cell._tc is listed._tc for listed in cells)
