from unittest import TestCase

from src.infrastructure.adapters.report.docx_report_adapter import DocxReportAdapter


class TestDocxReportAdapterInit(TestCase):
    def test_init_succeeds_without_logo_path(self):
        adapter = DocxReportAdapter(logo_path=None)
        self.assertIsInstance(adapter, DocxReportAdapter)
