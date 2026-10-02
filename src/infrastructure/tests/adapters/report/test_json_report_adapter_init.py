from unittest import TestCase

from src.infrastructure.adapters.report.json_report_adapter import JsonReportAdapter


class TestJsonReportAdapterInit(TestCase):
    def test_init_succeeds_with_no_arguments(self):
        adapter = JsonReportAdapter()

        self.assertIsInstance(adapter, JsonReportAdapter)
