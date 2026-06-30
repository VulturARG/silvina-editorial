from unittest import TestCase
from unittest.mock import MagicMock

from src.application.export_report_use_case import ExportReportUseCase
from src.domain.exceptions.base_src_error import SrcGenericError
from src.domain.exceptions.report_errors import ReportExportUnavailable
from src.domain.tests.report.fake_report_export_port import FakeReportExportPort


class TestExportReportUseCaseErrorPropagation(TestCase):
    def test_execute_propagates_report_export_unavailable_from_port(self):
        use_case = ExportReportUseCase(
            report_export_port=FakeReportExportPort(raise_error=ReportExportUnavailable())
        )
        with self.assertRaises(ReportExportUnavailable):
            use_case.execute(report_input=MagicMock(), output_path="out.docx")

    def test_execute_wraps_unexpected_exception_as_src_generic_error(self):
        use_case = ExportReportUseCase(
            report_export_port=FakeReportExportPort(raise_error=RuntimeError("unexpected"))
        )
        with self.assertRaises(SrcGenericError):
            use_case.execute(report_input=MagicMock(), output_path="out.docx")
