from os.path import join
from tempfile import TemporaryDirectory
from unittest import TestCase

from docx import Document
from docx.shared import Pt
from docx.styles.style import ParagraphStyle

from src.infrastructure.tests.adapters.report.fixtures import ReportFixtures


class TestDocxReportAdapterSettings(TestCase):
    def setUp(self) -> None:
        self._temporary_directory = TemporaryDirectory()
        self.addCleanup(self._temporary_directory.cleanup)
        self._output_path = join(self._temporary_directory.name, "report.docx")

    def test_export_applies_base_font_settings_to_normal_style(self):
        settings = ReportFixtures.make_settings(
            font_name="Arial", base_font_size_pt=11, line_spacing=1.5
        )
        adapter = ReportFixtures.make_adapter(docx_report_settings=settings)

        adapter.export(
            report_input=ReportFixtures.make_report_input_dto(), output_path=self._output_path
        )

        normal_style = Document(self._output_path).styles["Normal"]
        assert isinstance(normal_style, ParagraphStyle)
        self.assertEqual(normal_style.font.name, "Arial")
        self.assertEqual(normal_style.font.size, Pt(11))
        self.assertEqual(normal_style.paragraph_format.line_spacing, 1.5)
        self.assertEqual(normal_style.paragraph_format.space_after, Pt(0))
        self.assertEqual(normal_style.paragraph_format.space_before, Pt(0))
