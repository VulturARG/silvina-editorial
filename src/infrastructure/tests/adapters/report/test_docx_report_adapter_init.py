from typing import Any
from unittest import TestCase
from unittest.mock import patch

from src.domain.exceptions.report_errors import ReportExportUnavailable
from src.infrastructure.adapters.report.docx_report_adapter import DocxReportAdapter
from src.infrastructure.tests.adapters.report.fixtures import ReportFixtures


class TestDocxReportAdapterInit(TestCase):
    def test_init_succeeds_without_logo_path(self):
        adapter = ReportFixtures.make_adapter()
        self.assertIsInstance(adapter, DocxReportAdapter)

    @patch("src.infrastructure.adapters.report.docx_report_adapter.DOCX_AVAILABLE", False)
    def test_init_raises_report_export_unavailable_when_docx_missing(self):
        with self.assertRaises(ReportExportUnavailable):
            ReportFixtures.make_adapter()

    def test_init_requires_settings(self):
        kwargs: dict[str, Any] = {"logo_path": None}
        with self.assertRaises(TypeError):
            DocxReportAdapter(**kwargs)
