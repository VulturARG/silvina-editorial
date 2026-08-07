from unittest import TestCase

from src.application.export_report_use_case import ExportReportUseCase
from src.infrastructure.adapters.report.json_report_adapter import JsonReportAdapter
from src.infrastructure.wirings.json_report_wiring import JsonReportWiring


class TestJsonReportWiring(TestCase):
    def test_create_use_case_returns_export_report_use_case_instance(self):
        result = JsonReportWiring().create_use_case()
        self.assertEqual(type(result), ExportReportUseCase)

    def test_create_use_case_wires_json_report_adapter_as_port(self):
        result = JsonReportWiring().create_use_case()
        self.assertIsInstance(result._report_export_port, JsonReportAdapter)
