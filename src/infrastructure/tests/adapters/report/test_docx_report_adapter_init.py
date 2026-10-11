from unittest import TestCase

from src.infrastructure.adapters.report.docx_report_adapter import DocxReportAdapter
from src.infrastructure.tests.adapters.report.fixtures import ReportFixtures


class TestDocxReportAdapterInit(TestCase):
    def test_init_succeeds_with_page_decorations_and_sections(self):
        adapter = ReportFixtures.make_adapter()
        self.assertIsInstance(adapter, DocxReportAdapter)

    def test_init_accepts_empty_page_decorations_and_sections(self):
        adapter = DocxReportAdapter(page_decorations=(), sections=())
        self.assertIsInstance(adapter, DocxReportAdapter)
