from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from src.infrastructure.cli.document_analysis_command import DocumentAnalysisCommand
from src.infrastructure.wirings.document_analysis_command_wiring import (
    DocumentAnalysisCommandWiring,
)


class TestDocumentAnalysisCommandWiring(TestCase):
    def test_create_command_returns_document_analysis_command(self):
        command = DocumentAnalysisCommandWiring().create_command()

        self.assertIsInstance(command, DocumentAnalysisCommand)

    def test_services_factory_forwards_environment_and_prompt_file_overrides(self):
        wiring = DocumentAnalysisCommandWiring()
        environment_overrides = {"OLLAMA_MODEL_NAME": "custom"}
        prompt_file_overrides = {"s4_s5_s6_signal_prompt": Path("custom.txt")}
        with patch(
            "src.infrastructure.wirings.document_analysis_command_wiring.CliAnalysisServicesWiring"
        ) as mock_cli_wiring:
            wiring._create_services(environment_overrides, prompt_file_overrides, None)

        mock_cli_wiring.assert_called_once_with(environment_overrides, prompt_file_overrides, None)
        mock_cli_wiring.return_value.create_services.assert_called_once_with()

    def test_services_factory_forwards_prompts_root(self):
        wiring = DocumentAnalysisCommandWiring()
        prompts_root = Path("custom-prompts")
        with patch(
            "src.infrastructure.wirings.document_analysis_command_wiring.CliAnalysisServicesWiring"
        ) as mock_cli_wiring:
            wiring._create_services({}, {}, prompts_root)

        mock_cli_wiring.assert_called_once_with({}, {}, prompts_root)
        mock_cli_wiring.return_value.create_services.assert_called_once_with()
