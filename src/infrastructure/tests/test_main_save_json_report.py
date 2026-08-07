from unittest import TestCase
from unittest.mock import MagicMock, patch

from main import SilvinaEditorialAssistant


class TestMainSaveJsonReport(TestCase):
    def _build_assistant(self, json_use_case: MagicMock) -> SilvinaEditorialAssistant:
        with (
            patch(
                "src.infrastructure.wirings.analyze_document_use_case_wiring."
                "AnalyzeDocumentUseCaseWiring.create_use_case",
                return_value=MagicMock(),
            ),
            patch(
                "src.infrastructure.wirings.export_report_wiring."
                "ExportReportWiring.create_use_case",
                return_value=MagicMock(),
            ),
            patch(
                "src.infrastructure.wirings.json_report_wiring.JsonReportWiring.create_use_case",
                return_value=json_use_case,
            ),
        ):
            return SilvinaEditorialAssistant()

    def test_save_json_report_invokes_json_use_case_with_last_report_input_and_output_path(self):
        json_use_case = MagicMock()
        assistant = self._build_assistant(json_use_case)
        last_report_input = object()
        assistant._last_report_input = last_report_input

        assistant.save_json_report({}, "output/report.json")

        json_use_case.execute.assert_called_once_with(
            report_input=last_report_input, output_path="output/report.json"
        )

    def test_prepare_for_json_attribute_removed_from_silvina_editorial_assistant(self):
        self.assertFalse(hasattr(SilvinaEditorialAssistant, "_prepare_for_json"))
