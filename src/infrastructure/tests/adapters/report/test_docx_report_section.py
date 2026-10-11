from abc import ABC
from unittest import TestCase

from src.infrastructure.adapters.report.docx_report_section import DocxReportSection


class TestDocxReportSection(TestCase):
    def test_is_abstract_base_class(self) -> None:
        self.assertTrue(issubclass(DocxReportSection, ABC))

    def test_declares_render_as_its_only_abstract_method(self) -> None:
        self.assertEqual(DocxReportSection.__abstractmethods__, frozenset({"render"}))
