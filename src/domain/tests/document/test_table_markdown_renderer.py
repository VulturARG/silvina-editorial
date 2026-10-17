from unittest import TestCase

from src.domain.document.table_markdown_renderer import TableMarkdownRenderer
from src.domain.dtos.document_table_dto import DocumentTableDTO


def _build_table(rows: tuple[tuple[str, ...], ...], position: int = 0) -> DocumentTableDTO:
    return DocumentTableDTO(rows=rows, position=position)


class TestTableMarkdownRenderer(TestCase):
    def setUp(self):
        self._renderer = TableMarkdownRenderer()

    def test_renders_header_separator_and_one_line_per_data_row(self):
        table = _build_table((("Name", "Score"), ("Ana", "9"), ("Luis", "7")))

        markdown = self._renderer.render(table)

        self.assertEqual(
            markdown,
            "| Name | Score |\n| --- | --- |\n| Ana | 9 |\n| Luis | 7 |",
        )

    def test_pads_short_data_row_with_empty_cells_up_to_widest_row(self):
        table = _build_table((("Group", "A", "B"), ("Merged",), ("x", "y", "z")))

        markdown = self._renderer.render(table)

        self.assertEqual(
            markdown,
            "| Group | A | B |\n| --- | --- | --- |\n| Merged |  |  |\n| x | y | z |",
        )

    def test_pads_short_header_row_so_every_line_has_the_same_columns(self):
        table = _build_table((("Title",), ("a", "b")))

        markdown = self._renderer.render(table)

        self.assertEqual(markdown, "| Title |  |\n| --- | --- |\n| a | b |")

    def test_escapes_pipe_inside_cell(self):
        table = _build_table((("Expression", "Result"), ("a|b", "c")))

        markdown = self._renderer.render(table)

        self.assertEqual(markdown, "| Expression | Result |\n| --- | --- |\n| a\\|b | c |")

    def test_collapses_line_breaks_inside_cell_to_single_space(self):
        table = _build_table((("Header",), ("first line\nsecond line",)))

        markdown = self._renderer.render(table)

        self.assertEqual(markdown, "| Header |\n| --- |\n| first line second line |")

    def test_collapses_whitespace_runs_inside_cell_to_single_space(self):
        table = _build_table((("Header",), ("tab\tand\r\n   spaces",)))

        markdown = self._renderer.render(table)

        self.assertEqual(markdown, "| Header |\n| --- |\n| tab and spaces |")

    def test_strips_surrounding_spaces_from_cells(self):
        table = _build_table((("  Name  ", " Value "), ("  x ", "  ")))

        markdown = self._renderer.render(table)

        self.assertEqual(markdown, "| Name | Value |\n| --- | --- |\n| x |  |")

    def test_renders_single_row_table_as_header_and_separator_only(self):
        table = _build_table((("Only", "Header"),))

        markdown = self._renderer.render(table)

        self.assertEqual(markdown, "| Only | Header |\n| --- | --- |")

    def test_position_does_not_appear_in_output(self):
        table = _build_table((("a", "b"), ("1", "2")), position=42)

        markdown = self._renderer.render(table)

        self.assertEqual(markdown, "| a | b |\n| --- | --- |\n| 1 | 2 |")

    def test_returns_empty_string_for_table_without_rows(self):
        markdown = self._renderer.render(_build_table(()))

        self.assertEqual(markdown, "")
