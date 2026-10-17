from src.domain.dtos.document_table_dto import DocumentTableDTO


class TableMarkdownRenderer:
    """Domain service that renders a document table as a Markdown table."""

    _SEPARATOR_CELL = "---"
    _ESCAPED_PIPE = "\\|"

    def render(self, table: DocumentTableDTO) -> str:
        """Return the table as Markdown: header line, separator line, then one line per data row."""
        column_count = max((len(row) for row in table.rows), default=0)
        if column_count == 0:
            return ""
        padded_rows = [self._pad_row(row, column_count) for row in table.rows]
        header_line = self._format_line(padded_rows[0])
        separator_line = self._format_line((self._SEPARATOR_CELL,) * column_count)
        data_lines = [self._format_line(row) for row in padded_rows[1:]]
        return "\n".join([header_line, separator_line, *data_lines])

    def _pad_row(self, row: tuple[str, ...], column_count: int) -> tuple[str, ...]:
        return row + ("",) * (column_count - len(row))

    def _format_line(self, cells: tuple[str, ...]) -> str:
        return "| " + " | ".join(self._normalize_cell(cell) for cell in cells) + " |"

    def _normalize_cell(self, cell: str) -> str:
        return " ".join(cell.split()).replace("|", self._ESCAPED_PIPE)
