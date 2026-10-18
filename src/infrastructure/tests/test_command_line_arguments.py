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

    def test_prompt_file_overrides_maps_given_paths_to_field_names(self):
        arguments = CommandLineArguments(
            s4_s5_s6_signal_prompt=Path("prompts/signals"),
            alignment_prompt=Path("prompts/alignment"),
            argumentation_conclusions_prompt=Path("prompts/argumentation"),
            clarity_coherence_prompt=Path("prompts/clarity"),
            contribution_prompt=Path("prompts/contribution"),
            research_lines=Path("prompts/research"),
        )

        self.assertEqual(
            arguments.prompt_file_overrides(),
            {
                "s4_s5_s6_signal_prompt": Path("prompts/signals/s4_s5_s6_signal_prompt.txt"),
                "alignment_prompt": Path("prompts/alignment/alignment_prompt.txt"),
                "argumentation_conclusions_prompt": Path(
                    "prompts/argumentation/argumentation_conclusions_prompt.txt"
                ),
                "clarity_coherence_prompt": Path("prompts/clarity/clarity_coherence_prompt.txt"),
                "contribution_prompt": Path("prompts/contribution/contribution_prompt.txt"),
                "research_lines": Path("prompts/research/research_lines.txt"),
            },
        )

    def test_prompt_file_overrides_maps_omitted_values_to_none(self):
        self.assertEqual(
            CommandLineArguments().prompt_file_overrides(),
            {
                "s4_s5_s6_signal_prompt": None,
                "alignment_prompt": None,
                "argumentation_conclusions_prompt": None,
                "clarity_coherence_prompt": None,
                "contribution_prompt": None,
                "research_lines": None,
            },
        )

    def test_prompt_file_overrides_exposes_only_the_six_prompt_keys(self):
        arguments = CommandLineArguments(
            document_name="report.docx",
            input_directory=Path("input"),
            output_directory=Path("output"),
        )

        self.assertEqual(
            set(arguments.prompt_file_overrides()),
            {
                "s4_s5_s6_signal_prompt",
                "alignment_prompt",
                "argumentation_conclusions_prompt",
                "clarity_coherence_prompt",
                "contribution_prompt",
                "research_lines",
            },
        )

    def test_prompts_directory_is_none_when_omitted(self):
        self.assertIsNone(CommandLineArguments().prompts_directory)

    def test_prompt_root_relative_paths_lists_six_files_grouped_by_folder(self):
        self.assertEqual(
            CommandLineArguments.prompt_root_relative_paths(),
            (
                Path("classification/s4_s5_s6_signal_prompt.txt"),
                Path("quality/alignment_prompt.txt"),
                Path("quality/argumentation_conclusions_prompt.txt"),
                Path("quality/clarity_coherence_prompt.txt"),
                Path("quality/contribution_prompt.txt"),
                Path("quality/research_lines.txt"),
            ),
        )
