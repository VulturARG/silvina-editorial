from unittest import TestCase

from src.domain.exceptions.base_src_error import SrcBaseWarning
from src.domain.exceptions.report_errors import ReportExportUnavailable


class TestReportExportUnavailable(TestCase):
    def test_message_equals_expected_string(self):
        expected = "The report export service is unavailable (python-docx not installed)."
        self.assertEqual(ReportExportUnavailable.MESSAGE, expected)

    def test_is_instance_of_src_base_warning(self):
        exc = ReportExportUnavailable()
        self.assertIsInstance(exc, SrcBaseWarning)
