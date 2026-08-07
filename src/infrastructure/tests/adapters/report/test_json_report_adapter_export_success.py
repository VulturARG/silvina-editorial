from json import load
from os import remove
from unittest import TestCase

from src.infrastructure.adapters.report.json_report_adapter import JsonReportAdapter
from src.infrastructure.tests.adapters.report.json_fixtures import JsonReportFixtures

_OUTPUT_PATH = "test_json_report_adapter_export_success_output.json"


class TestJsonReportAdapterExportSuccess(TestCase):
    def tearDown(self):
        try:
            remove(_OUTPUT_PATH)
        except FileNotFoundError:
            pass

    def test_export_returns_true_and_writes_file(self):
        adapter = JsonReportAdapter()
        report_input = JsonReportFixtures.make_real_report_input_dto()

        result = adapter.export(report_input=report_input, output_path=_OUTPUT_PATH)

        self.assertTrue(result)
        with open(_OUTPUT_PATH, encoding="utf-8") as file:
            written_data = load(file)
        self.assertEqual(written_data["filename"], "sample_article.docx")

    def test_export_writes_legacy_shape_top_level_keys(self):
        adapter = JsonReportAdapter()
        report_input = JsonReportFixtures.make_real_report_input_dto()

        adapter.export(report_input=report_input, output_path=_OUTPUT_PATH)

        with open(_OUTPUT_PATH, encoding="utf-8") as file:
            written_data = load(file)
        self.assertEqual(
            set(written_data.keys()),
            {
                "filename",
                "document_info",
                "classification",
                "quality_analysis",
                "structure_validation",
                "citations_analysis",
                "apa_validation",
                "recommendations",
            },
        )

    def test_export_converts_enum_fields_to_strings(self):
        adapter = JsonReportAdapter()
        report_input = JsonReportFixtures.make_real_report_input_dto()

        adapter.export(report_input=report_input, output_path=_OUTPUT_PATH)

        with open(_OUTPUT_PATH, encoding="utf-8") as file:
            written_data = load(file)
        self.assertEqual(written_data["classification"]["category"], "científico")
        self.assertEqual(written_data["classification"]["article_size"], "corto")
        self.assertEqual(written_data["quality_analysis"]["quality_level"], "Bueno")
        self.assertEqual(
            written_data["apa_validation"]["violations"][0]["error_type"], "Puntuación incorrecta"
        )
        self.assertEqual(written_data["recommendations"][0]["priority"], "alta")
