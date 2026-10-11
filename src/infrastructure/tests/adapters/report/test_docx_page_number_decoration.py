from unittest import TestCase

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor
from docx.text.paragraph import Paragraph

from src.infrastructure.adapters.report.docx_page_decoration import DocxPageDecoration
from src.infrastructure.tests.adapters.report.fixtures import ReportFixtures


class TestDocxPageNumberDecoration(TestCase):
    def setUp(self) -> None:
        self.settings = ReportFixtures.make_settings()
        self.decoration = ReportFixtures.make_page_number_decoration(
            docx_report_settings=self.settings
        )
        self.document = Document()
        self.decoration.apply(document=self.document)

    def _footer_paragraph(self) -> Paragraph:
        return self.document.sections[0].footer.paragraphs[0]

    def test_is_docx_page_decoration(self) -> None:
        self.assertIsInstance(self.decoration, DocxPageDecoration)

    def test_apply_centers_footer_paragraph(self) -> None:
        self.assertEqual(self._footer_paragraph().alignment, WD_ALIGN_PARAGRAPH.CENTER)

    def test_apply_writes_page_field_separator_and_total_pages_field_in_order(self) -> None:
        field_runs = self._footer_paragraph()._element.xpath("./w:r")

        field_run_tags = [qn("w:fldChar"), qn("w:instrText"), qn("w:fldChar")]
        self.assertEqual(
            [[child.tag for child in run if child.tag != qn("w:rPr")] for run in field_runs],
            [field_run_tags, [qn("w:t")], field_run_tags],
        )
        self.assertEqual(self._footer_paragraph().text, " de ")

    def test_apply_writes_page_and_numpages_field_instructions(self) -> None:
        instructions = self._footer_paragraph()._element.xpath(".//w:instrText")

        self.assertEqual([instruction.text for instruction in instructions], ["PAGE", "NUMPAGES"])

    def test_apply_wraps_each_field_instruction_between_begin_and_end_characters(self) -> None:
        field_character_types = self._footer_paragraph()._element.xpath(
            ".//w:fldChar/@w:fldCharType"
        )

        self.assertEqual(field_character_types, ["begin", "end", "begin", "end"])

    def test_apply_styles_every_footer_run_as_page_number_metadata(self) -> None:
        footer_runs = self._footer_paragraph().runs

        self.assertEqual(len(footer_runs), 3)
        for run in footer_runs:
            self.assertEqual(run.font.size, Pt(self.settings.page_number_font_size_pt))
            self.assertEqual(run.font.color.rgb, RGBColor(*self.settings.neutral_color_rgb))
