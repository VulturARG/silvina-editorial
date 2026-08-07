from unittest import TestCase

from src.infrastructure.adapters.report.json_report_adapter import JsonReportAdapter
from src.infrastructure.tests.adapters.report.json_fixtures import JsonReportFixtures


class TestJsonReportAdapterExportFailure(TestCase):
    def test_export_raises_os_error_when_path_is_unwritable(self):
        adapter = JsonReportAdapter()
        report_input = JsonReportFixtures.make_real_report_input_dto()

        with self.assertRaises(OSError):
            adapter.export(
                report_input=report_input,
                output_path="nonexistent_directory/nested/output.json",
            )
