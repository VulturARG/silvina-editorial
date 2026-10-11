from unittest import TestCase

from docx import Document
from docx.shared import Pt
from docx.styles.style import ParagraphStyle

from src.infrastructure.adapters.report.docx_page_decoration import DocxPageDecoration
from src.infrastructure.tests.adapters.report.fixtures import ReportFixtures


class TestDocxBaseStyleDecoration(TestCase):
    def setUp(self) -> None:
        self.settings = ReportFixtures.make_settings(
            font_name="Arial", base_font_size_pt=11, line_spacing=1.5
        )
        self.decoration = ReportFixtures.make_base_style_decoration(
            docx_report_settings=self.settings
        )
        self.document = Document()

    def _normal_style(self) -> ParagraphStyle:
        normal_style = self.document.styles["Normal"]
        assert isinstance(normal_style, ParagraphStyle)
        return normal_style

    def test_is_docx_page_decoration(self) -> None:
        self.assertIsInstance(self.decoration, DocxPageDecoration)

    def test_apply_sets_normal_style_font_from_settings(self) -> None:
        self.decoration.apply(document=self.document)

        normal_style = self._normal_style()
        self.assertEqual(normal_style.font.name, "Arial")
        self.assertEqual(normal_style.font.size, Pt(11))

    def test_apply_sets_normal_style_line_spacing_from_settings(self) -> None:
        self.decoration.apply(document=self.document)

        self.assertEqual(self._normal_style().paragraph_format.line_spacing, 1.5)

    def test_apply_removes_normal_style_space_before_and_after(self) -> None:
        self.decoration.apply(document=self.document)

        normal_style = self._normal_style()
        self.assertEqual(normal_style.paragraph_format.space_after, Pt(0))
        self.assertEqual(normal_style.paragraph_format.space_before, Pt(0))
