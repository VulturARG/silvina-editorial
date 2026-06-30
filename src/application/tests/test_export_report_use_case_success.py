from unittest import TestCase
from unittest.mock import MagicMock

from src.application.export_report_use_case import ExportReportUseCase
from src.domain.tests.report.fake_report_export_port import FakeReportExportPort


class TestExportReportUseCaseSuccess(TestCase):
    def test_execute_returns_true_when_port_returns_true(self):
        use_case = ExportReportUseCase(report_export_port=FakeReportExportPort(return_value=True))
        result = use_case.execute(report_input=MagicMock(), output_path="out.docx")
        self.assertTrue(result)

    def test_execute_returns_false_when_port_returns_false(self):
        use_case = ExportReportUseCase(report_export_port=FakeReportExportPort(return_value=False))
        result = use_case.execute(report_input=MagicMock(), output_path="out.docx")
        self.assertFalse(result)
