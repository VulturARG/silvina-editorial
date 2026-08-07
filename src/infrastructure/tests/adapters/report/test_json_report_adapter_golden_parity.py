from os import remove
from pathlib import Path
from unittest import TestCase

from src.infrastructure.adapters.report.json_report_adapter import JsonReportAdapter
from src.infrastructure.tests.adapters.report.json_fixtures import JsonReportFixtures

_GOLDEN_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "json_export_golden.json"
_OUTPUT_PATH = "test_json_report_adapter_golden_parity_output.json"


class TestJsonReportAdapterGoldenParity(TestCase):
    def tearDown(self):
        try:
            remove(_OUTPUT_PATH)
        except FileNotFoundError:
            pass

    def test_export_output_is_byte_identical_to_golden_fixture(self):
        adapter = JsonReportAdapter()
        report_input = JsonReportFixtures.make_real_report_input_dto()

        adapter.export(report_input=report_input, output_path=_OUTPUT_PATH)

        with open(_OUTPUT_PATH, "rb") as file:
            actual_bytes = file.read()
        with open(_GOLDEN_FIXTURE_PATH, "rb") as file:
            golden_bytes = file.read()
        self.assertEqual(actual_bytes, golden_bytes)
