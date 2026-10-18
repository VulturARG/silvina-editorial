from json import load
from os.path import join
from tempfile import TemporaryDirectory
from unittest import TestCase

from src.application.export_report_use_case import ExportReportUseCase
from src.domain.dtos.prompt_source_dto import PromptSourceDTO
from src.infrastructure.adapters.report.json_report_adapter import JsonReportAdapter
from src.infrastructure.tests.adapters.report.json_fixtures import JsonReportFixtures
from src.infrastructure.wirings.json_report_wiring import JsonReportWiring


class TestJsonReportWiring(TestCase):
    def test_create_use_case_returns_export_report_use_case_instance(self):
        result = JsonReportWiring().create_use_case()
        self.assertEqual(type(result), ExportReportUseCase)

    def test_create_use_case_wires_json_report_adapter_as_port(self):
        result = JsonReportWiring().create_use_case()
        self.assertIsInstance(result._report_export_port, JsonReportAdapter)

    def test_create_use_case_writes_prompt_source_when_given(self):
        prompt_source = PromptSourceDTO(base_label="v2", replaced_prompt_names=())
        use_case = JsonReportWiring(prompt_source=prompt_source).create_use_case()

        written_data = self._export_with(use_case)

        self.assertEqual(written_data["prompt_source"], "v2")

    def test_create_use_case_writes_no_prompt_source_key_without_prompt_source(self):
        use_case = JsonReportWiring().create_use_case()

        written_data = self._export_with(use_case)

        self.assertNotIn("prompt_source", written_data)

    @staticmethod
    def _export_with(use_case):
        with TemporaryDirectory() as temporary_directory:
            output_path = join(temporary_directory, "report.json")
            use_case.execute(
                report_input=JsonReportFixtures.make_real_report_input_dto(),
                output_path=output_path,
            )
            with open(output_path, encoding="utf-8") as file:
                return load(file)
