from unittest import TestCase

from src.domain.report.report_export_port import ReportExportPort


class TestReportExportPort(TestCase):
    def test_cannot_instantiate_abstract_port_directly(self):
        with self.assertRaises(TypeError):
            ReportExportPort()  # type: ignore[abstract]
