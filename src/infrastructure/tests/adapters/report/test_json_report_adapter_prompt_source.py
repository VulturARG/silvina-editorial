from json import load
from os import path
from tempfile import TemporaryDirectory
from unittest import TestCase

from src.domain.dtos.prompt_source_dto import PromptSourceDTO
from src.infrastructure.adapters.report.json_report_adapter import JsonReportAdapter
from src.infrastructure.tests.adapters.report.json_fixtures import JsonReportFixtures


class TestJsonReportAdapterPromptSource(TestCase):
    def setUp(self):
        self._temporary_directory = TemporaryDirectory()
        self.addCleanup(self._temporary_directory.cleanup)
        self._output_path = path.join(self._temporary_directory.name, "report.json")
        self._report_input = JsonReportFixtures.make_real_report_input_dto()

    def test_export_writes_prompt_source_description_when_present(self):
        adapter = JsonReportAdapter(
            prompt_source=PromptSourceDTO(
                base_label="v2", replaced_prompt_names=("alignment_prompt",)
            )
        )

        written_data = self._export_data(adapter)

        self.assertEqual(written_data["prompt_source"], "v2 + alignment_prompt")

    def test_export_omits_prompt_source_key_when_absent(self):
        written_data = self._export_data(JsonReportAdapter())

        self.assertNotIn("prompt_source", written_data)

    def test_export_adds_only_prompt_source_key_when_present(self):
        without_prompt_source = self._export_data(JsonReportAdapter())
        with_prompt_source = self._export_data(
            JsonReportAdapter(
                prompt_source=PromptSourceDTO(base_label="default", replaced_prompt_names=())
            )
        )

        self.assertEqual(
            set(with_prompt_source.keys()),
            set(without_prompt_source.keys()) | {"prompt_source"},
        )

    def _export_data(self, adapter):
        adapter.export(report_input=self._report_input, output_path=self._output_path)
        with open(self._output_path, encoding="utf-8") as file:
            return load(file)
