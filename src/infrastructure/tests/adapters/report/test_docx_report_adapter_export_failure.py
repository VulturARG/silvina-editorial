from unittest import TestCase
from unittest.mock import MagicMock, patch

from src.infrastructure.adapters.report.docx_report_adapter import DocxReportAdapter
from src.infrastructure.tests.adapters.report.fixtures import ReportFixtures


class TestDocxReportAdapterExportFailure(TestCase):
    @patch("src.infrastructure.adapters.report.docx_report_adapter.Document")
    def test_export_raises_os_error_on_io_failure(self, mock_document_class):
        mock_doc = MagicMock()
        mock_doc.save.side_effect = OSError("Disk full")
        mock_document_class.return_value = mock_doc

        adapter = DocxReportAdapter(logo_path=None)
        with self.assertRaises(OSError):
            adapter.export(
                report_input=ReportFixtures.make_report_input_dto(), output_path="output.docx"
            )
