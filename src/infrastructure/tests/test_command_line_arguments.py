from pathlib import Path
from unittest import TestCase

from src.infrastructure.cli.command_line_arguments import CommandLineArguments


class TestCommandLineArguments(TestCase):
    def test_environment_overrides_maps_given_values_to_environment_variable_names(self):
        arguments = CommandLineArguments(
            document_name="report.docx",
            input_directory=Path("input"),
            output_directory=Path("output"),
            ollama_model_name="gemma-test",
            use_external_llm=True,
            llm_provider="anthropic",
            external_llm_model_name="claude-test",
            app_mode="DEBUG",
        )

        self.assertEqual(
            arguments.environment_overrides(),
            {
                "OLLAMA_MODEL_NAME": "gemma-test",
                "USE_EXTERNAL_LLM": "true",
                "LLM_PROVIDER": "anthropic",
                "EXTERNAL_LLM_MODEL_NAME": "claude-test",
                "APP_MODE": "DEBUG",
            },
        )

    def test_use_external_llm_false_is_mapped_to_lowercase_text(self):
        arguments = CommandLineArguments(use_external_llm=False)

        self.assertEqual(arguments.environment_overrides()["USE_EXTERNAL_LLM"], "false")

    def test_environment_overrides_maps_omitted_values_to_none(self):
        self.assertEqual(
            CommandLineArguments().environment_overrides(),
            {
                "OLLAMA_MODEL_NAME": None,
                "USE_EXTERNAL_LLM": None,
                "LLM_PROVIDER": None,
                "EXTERNAL_LLM_MODEL_NAME": None,
                "APP_MODE": None,
            },
        )

    def test_environment_overrides_exposes_only_the_five_override_keys(self):
        arguments = CommandLineArguments(
            document_name="report.docx",
            input_directory=Path("input"),
            output_directory=Path("output"),
        )

        self.assertEqual(
            set(arguments.environment_overrides()),
            {
                "OLLAMA_MODEL_NAME",
                "USE_EXTERNAL_LLM",
                "LLM_PROVIDER",
                "EXTERNAL_LLM_MODEL_NAME",
                "APP_MODE",
            },
        )
