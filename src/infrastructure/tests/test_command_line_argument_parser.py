from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
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

    def test_parses_s4_s5_s6_signal_prompt_as_directory_path(self):
        temporary_directory = TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        prompt_directory = Path(temporary_directory.name)
        prompt_file = prompt_directory / "s4_s5_s6_signal_prompt.txt"
        prompt_file.write_text("signal", encoding="utf-8")

        arguments = self.parser.parse(["--s4-s5-s6-signal-prompt", str(prompt_directory)])

        self.assertEqual(arguments.s4_s5_s6_signal_prompt, prompt_directory)

    def test_parses_alignment_prompt_as_directory_path(self):
        temporary_directory = TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        prompt_directory = Path(temporary_directory.name)
        prompt_file = prompt_directory / "alignment_prompt.txt"
        prompt_file.write_text("alignment", encoding="utf-8")

        arguments = self.parser.parse(["--alignment-prompt", str(prompt_directory)])

        self.assertEqual(arguments.alignment_prompt, prompt_directory)

    def test_parses_argumentation_conclusions_prompt_as_directory_path(self):
        temporary_directory = TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        prompt_directory = Path(temporary_directory.name)
        prompt_file = prompt_directory / "argumentation_conclusions_prompt.txt"
        prompt_file.write_text("argumentation", encoding="utf-8")

        arguments = self.parser.parse(["--argumentation-conclusions-prompt", str(prompt_directory)])

        self.assertEqual(arguments.argumentation_conclusions_prompt, prompt_directory)

    def test_parses_clarity_coherence_prompt_as_directory_path(self):
        temporary_directory = TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        prompt_directory = Path(temporary_directory.name)
        prompt_file = prompt_directory / "clarity_coherence_prompt.txt"
        prompt_file.write_text("clarity", encoding="utf-8")

        arguments = self.parser.parse(["--clarity-coherence-prompt", str(prompt_directory)])

        self.assertEqual(arguments.clarity_coherence_prompt, prompt_directory)

    def test_parses_contribution_prompt_as_directory_path(self):
        temporary_directory = TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        prompt_directory = Path(temporary_directory.name)
        prompt_file = prompt_directory / "contribution_prompt.txt"
        prompt_file.write_text("contribution", encoding="utf-8")

        arguments = self.parser.parse(["--contribution-prompt", str(prompt_directory)])

        self.assertEqual(arguments.contribution_prompt, prompt_directory)

    def test_parses_research_lines_as_directory_path(self):
        temporary_directory = TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        prompt_directory = Path(temporary_directory.name)
        prompt_file = prompt_directory / "research_lines.txt"
        prompt_file.write_text("lines", encoding="utf-8")

        arguments = self.parser.parse(["--research-lines", str(prompt_directory)])

        self.assertEqual(arguments.research_lines, prompt_directory)

    def test_rejects_prompt_directory_that_does_not_exist(self):
        temporary_directory = TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        nonexistent_directory = Path(temporary_directory.name) / "nonexistent"

        self._assert_usage_error(["--s4-s5-s6-signal-prompt", str(nonexistent_directory)])

    def test_rejects_prompt_directory_path_that_is_a_file(self):
        temporary_directory = TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        file_path = Path(temporary_directory.name) / "a_file.txt"
        file_path.write_text("content", encoding="utf-8")

        self._assert_usage_error(["--s4-s5-s6-signal-prompt", str(file_path)])

    def test_rejects_prompt_directory_missing_expected_file(self):
        temporary_directory = TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        prompt_directory = Path(temporary_directory.name) / "prompts"
        prompt_directory.mkdir()
        (prompt_directory / "another.txt").write_text("other", encoding="utf-8")

        self._assert_usage_error(["--s4-s5-s6-signal-prompt", str(prompt_directory)])

    def test_rejects_prompt_directory_having_only_file_for_another_option(self):
        temporary_directory = TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        prompt_directory = Path(temporary_directory.name) / "prompts"
        prompt_directory.mkdir()
        (prompt_directory / "alignment_prompt.txt").write_text("other", encoding="utf-8")

        self._assert_usage_error(["--s4-s5-s6-signal-prompt", str(prompt_directory)])

    def test_parses_all_prompt_options_together(self):
        temporary_directory = TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        base_directory = Path(temporary_directory.name)
        (base_directory / "s4_s5_s6_signal_prompt.txt").write_text("signal", encoding="utf-8")
        (base_directory / "alignment_prompt.txt").write_text("alignment", encoding="utf-8")
        (base_directory / "argumentation_conclusions_prompt.txt").write_text(
            "argumentation", encoding="utf-8"
        )
        (base_directory / "clarity_coherence_prompt.txt").write_text("clarity", encoding="utf-8")
        (base_directory / "contribution_prompt.txt").write_text("contribution", encoding="utf-8")
        (base_directory / "research_lines.txt").write_text("lines", encoding="utf-8")

        arguments = self.parser.parse(
            [
                "--s4-s5-s6-signal-prompt",
                str(base_directory),
                "--alignment-prompt",
                str(base_directory),
                "--argumentation-conclusions-prompt",
                str(base_directory),
                "--clarity-coherence-prompt",
                str(base_directory),
                "--contribution-prompt",
                str(base_directory),
                "--research-lines",
                str(base_directory),
            ]
        )

        self.assertEqual(
            arguments,
            CommandLineArguments(
                s4_s5_s6_signal_prompt=base_directory,
                alignment_prompt=base_directory,
                argumentation_conclusions_prompt=base_directory,
                clarity_coherence_prompt=base_directory,
                contribution_prompt=base_directory,
                research_lines=base_directory,
            ),
        )

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
