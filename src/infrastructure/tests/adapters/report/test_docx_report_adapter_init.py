from unittest import TestCase
from unittest.mock import MagicMock, patch

from src.domain.exceptions.report_errors import ReportExportUnavailable
from src.infrastructure.adapters.report.docx_report_adapter import DocxReportAdapter
from src.infrastructure.adapters.report.docx_report_section import DocxReportSection
from src.infrastructure.tests.adapters.report.fixtures import ReportFixtures


class TestDocxReportAdapterInit(TestCase):
    def test_init_succeeds_with_page_decorations_and_sections(self):
        adapter = ReportFixtures.make_adapter()
        self.assertIsInstance(adapter, DocxReportAdapter)

    @patch("src.infrastructure.adapters.report.docx_report_adapter.DOCX_AVAILABLE", False)
    def test_init_raises_report_export_unavailable_when_docx_missing(self):
        with self.assertRaises(ReportExportUnavailable):
            ReportFixtures.make_adapter()

    def test_init_requires_page_decorations(self):
        sections_without_page_decorations = {
            section_name: MagicMock(spec=DocxReportSection)
            for section_name in ReportFixtures.make_sections()
        }
        with self.assertRaises(TypeError):
            DocxReportAdapter(**sections_without_page_decorations)
