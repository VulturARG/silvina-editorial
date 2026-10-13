from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from unittest import TestCase

from src.infrastructure.cli.command_line_argument_parser import CommandLineArgumentParser
from src.infrastructure.cli.command_line_arguments import CommandLineArguments


class TestCommandLineArgumentParser(TestCase):
    def setUp(self):
        self.parser = CommandLineArgumentParser()

    def _assert_usage_error(self, argument_list: list[str]) -> None:
        with redirect_stderr(StringIO()), self.assertRaises(SystemExit):
            self.parser.parse(argument_list)

    def test_every_argument_is_none_when_omitted(self):
        self.assertEqual(self.parser.parse([]), CommandLineArguments())

    def test_parses_document_name_positional(self):
        arguments = self.parser.parse(["report.docx"])

        self.assertEqual(arguments.document_name, "report.docx")

    def test_parses_input_directory_as_path(self):
        arguments = self.parser.parse(["--input-dir", "input"])

        self.assertEqual(arguments.input_directory, Path("input"))

    def test_parses_output_directory_as_path(self):
        arguments = self.parser.parse(["--output-dir", "output"])

        self.assertEqual(arguments.output_directory, Path("output"))

    def test_parses_ollama_model_name(self):
        arguments = self.parser.parse(["--ollama-model-name", "gemma-test"])

        self.assertEqual(arguments.ollama_model_name, "gemma-test")

    def test_parses_llm_provider(self):
        arguments = self.parser.parse(["--llm-provider", "anthropic"])

        self.assertEqual(arguments.llm_provider, "anthropic")

    def test_parses_external_llm_model_name(self):
        arguments = self.parser.parse(["--external-llm-model-name", "claude-test"])

        self.assertEqual(arguments.external_llm_model_name, "claude-test")

    def test_parses_use_external_llm_true(self):
        arguments = self.parser.parse(["--use-external-llm", "true"])

        self.assertIs(arguments.use_external_llm, True)

    def test_parses_use_external_llm_false(self):
        arguments = self.parser.parse(["--use-external-llm", "false"])

        self.assertIs(arguments.use_external_llm, False)

    def test_parses_use_external_llm_case_insensitively(self):
        arguments = self.parser.parse(["--use-external-llm", "TRUE"])

        self.assertIs(arguments.use_external_llm, True)

    def test_rejects_use_external_llm_value_that_is_not_a_boolean(self):
        self._assert_usage_error(["--use-external-llm", "maybe"])

    def test_rejects_use_external_llm_without_value(self):
        self._assert_usage_error(["--use-external-llm"])

    def test_normalizes_app_mode_to_upper_case(self):
        arguments = self.parser.parse(["--app-mode", "debug"])

        self.assertEqual(arguments.app_mode, "DEBUG")

    def test_accepts_prod_app_mode_in_any_case(self):
        arguments = self.parser.parse(["--app-mode", "Prod"])

        self.assertEqual(arguments.app_mode, "PROD")

    def test_rejects_app_mode_that_is_not_debug_or_prod(self):
        self._assert_usage_error(["--app-mode", "staging"])

    def test_rejects_removed_word_report_path_option(self):
        self._assert_usage_error(["--word-report-path", "report.docx"])

    def test_rejects_removed_json_report_path_option(self):
        self._assert_usage_error(["--json-report-path", "report.json"])

    def test_parses_every_option_together(self):
        arguments = self.parser.parse(
            [
                "report.docx",
                "--input-dir",
                "input",
                "--output-dir",
                "output",
                "--ollama-model-name",
                "gemma-test",
                "--use-external-llm",
                "false",
                "--llm-provider",
                "anthropic",
                "--external-llm-model-name",
                "claude-test",
                "--app-mode",
                "debug",
            ]
        )

        self.assertEqual(
            arguments,
            CommandLineArguments(
                document_name="report.docx",
                input_directory=Path("input"),
                output_directory=Path("output"),
                ollama_model_name="gemma-test",
                use_external_llm=False,
                llm_provider="anthropic",
                external_llm_model_name="claude-test",
                app_mode="DEBUG",
            ),
        )
