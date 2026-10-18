from os import path
from tempfile import TemporaryDirectory
from unittest import TestCase

from src.application.export_report_use_case import ExportReportUseCase
from src.domain.dtos.prompt_source_dto import PromptSourceDTO
from src.infrastructure.adapters.report.html_report_adapter import HtmlReportAdapter
from src.infrastructure.tests.adapters.report.characterization_report_input import (
    CharacterizationReportInput,
)
from src.infrastructure.wirings.html_report_wiring import HtmlReportWiring


class TestHtmlReportWiring(TestCase):
    def test_create_use_case_returns_export_report_use_case_instance(self):
        result = HtmlReportWiring().create_use_case()

        self.assertEqual(type(result), ExportReportUseCase)

    def test_create_use_case_wires_html_report_adapter_as_port(self):
        result = HtmlReportWiring().create_use_case()

        self.assertIsInstance(result._report_export_port, HtmlReportAdapter)

    def test_exported_page_embeds_logo_and_stylesheet(self):
        use_case = HtmlReportWiring().create_use_case()
        with TemporaryDirectory() as temporary_directory:
            output_path = path.join(temporary_directory, "report.html")

            use_case.execute(
                report_input=CharacterizationReportInput.build(), output_path=output_path
            )

            with open(output_path, encoding="utf-8") as file:
                html = file.read()
        self.assertIn("data:image/png;base64,", html)
        self.assertIn("<style", html)
        self.assertNotIn("/reports/", html)

    def test_exported_page_shows_prompt_source_when_given(self):
        prompt_source = PromptSourceDTO(
            base_label="v2", replaced_prompt_names=("alignment_prompt",)
        )
        use_case = HtmlReportWiring(prompt_source=prompt_source).create_use_case()
        with TemporaryDirectory() as temporary_directory:
            output_path = path.join(temporary_directory, "report.html")

            use_case.execute(
                report_input=CharacterizationReportInput.build(), output_path=output_path
            )

            with open(output_path, encoding="utf-8") as file:
                html = file.read()
        self.assertIn("Prompts utilizados:", html)
        self.assertIn("v2 + alignment_prompt", html)
