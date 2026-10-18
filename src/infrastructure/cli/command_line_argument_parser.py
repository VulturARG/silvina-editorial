from argparse import ArgumentParser, ArgumentTypeError
from collections.abc import Sequence
from functools import partial
from pathlib import Path

from src.domain.enums.app_mode import AppMode
from src.infrastructure.cli.command_line_arguments import CommandLineArguments


class CommandLineArgumentParser:
    """Parse the command line of the Silvina Editorial Assistant into CommandLineArguments."""

    BOOLEAN_VALUES_BY_TEXT: dict[str, bool] = {"true": True, "false": False}

    def parse(self, argument_list: Sequence[str] | None = None) -> CommandLineArguments:
        """Parse the given arguments, or the process arguments when none are given."""
        namespace = self._build_argument_parser().parse_args(argument_list)
        return CommandLineArguments(
            document_name=namespace.document_name,
            input_directory=namespace.input_directory,
            output_directory=namespace.output_directory,
            ollama_model_name=namespace.ollama_model_name,
            use_external_llm=namespace.use_external_llm,
            llm_provider=namespace.llm_provider,
            external_llm_model_name=namespace.external_llm_model_name,
            app_mode=namespace.app_mode,
            s4_s5_s6_signal_prompt=namespace.s4_s5_s6_signal_prompt,
            alignment_prompt=namespace.alignment_prompt,
            argumentation_conclusions_prompt=namespace.argumentation_conclusions_prompt,
            clarity_coherence_prompt=namespace.clarity_coherence_prompt,
            contribution_prompt=namespace.contribution_prompt,
            research_lines=namespace.research_lines,
            prompts_directory=namespace.prompts_directory,
        )

    def _build_argument_parser(self) -> ArgumentParser:
        """Build the parser that declares every accepted option."""
        parser = ArgumentParser(
            description="Silvina Editorial Assistant - Academic document analysis"
        )
        parser.add_argument(
            "document_name",
            nargs="?",
            default=None,
            help="Name of the .docx document to analyze (asked on the console if omitted)",
        )
        parser.add_argument(
            "--input-dir",
            dest="input_directory",
            type=Path,
            default=None,
            help="Directory where the document is read (default: current directory)",
        )
        parser.add_argument(
            "--output-dir",
            dest="output_directory",
            type=Path,
            default=None,
            help="Directory for the reports (default: <document directory>/análisis)",
        )
        parser.add_argument(
            "--ollama-model-name",
            dest="ollama_model_name",
            default=None,
            help="Ollama model name that overrides OLLAMA_MODEL_NAME",
        )
        parser.add_argument(
            "--use-external-llm",
            dest="use_external_llm",
            type=self._parse_boolean_text,
            default=None,
            metavar="true|false",
            help="Whether to use the external LLM; overrides USE_EXTERNAL_LLM",
        )
        parser.add_argument(
            "--llm-provider",
            dest="llm_provider",
            default=None,
            help="LLM provider that overrides LLM_PROVIDER",
        )
        parser.add_argument(
            "--external-llm-model-name",
            dest="external_llm_model_name",
            default=None,
            help="External LLM model name that overrides EXTERNAL_LLM_MODEL_NAME",
        )
        parser.add_argument(
            "--app-mode",
            dest="app_mode",
            type=str.upper,
            choices=[mode.value for mode in AppMode],
            default=None,
            help="Application mode that overrides APP_MODE",
        )
        parser.add_argument(
            "--prompts-dir",
            dest="prompts_directory",
            type=self._parse_prompts_directory_path,
            default=None,
            metavar="DIRECTORY",
            help=(
                "Root of a complete prompt set: a directory with the classification/ and quality/ "
                "folders, holding the same file names as the default prompts"
            ),
        )
        parser.add_argument(
            "--s4-s5-s6-signal-prompt",
            dest="s4_s5_s6_signal_prompt",
            type=partial(
                self._parse_prompt_directory_path,
                expected_file_name="s4_s5_s6_signal_prompt.txt",
            ),
            default=None,
            metavar="DIRECTORY",
            help="Directory containing s4_s5_s6_signal_prompt.txt that overrides the default signal prompt",
        )
        parser.add_argument(
            "--alignment-prompt",
            dest="alignment_prompt",
            type=partial(
                self._parse_prompt_directory_path,
                expected_file_name="alignment_prompt.txt",
            ),
            default=None,
            metavar="DIRECTORY",
            help="Directory containing alignment_prompt.txt that overrides the default alignment prompt",
        )
        parser.add_argument(
            "--argumentation-conclusions-prompt",
            dest="argumentation_conclusions_prompt",
            type=partial(
                self._parse_prompt_directory_path,
                expected_file_name="argumentation_conclusions_prompt.txt",
            ),
            default=None,
            metavar="DIRECTORY",
            help="Directory containing argumentation_conclusions_prompt.txt that overrides the default prompt",
        )
        parser.add_argument(
            "--clarity-coherence-prompt",
            dest="clarity_coherence_prompt",
            type=partial(
                self._parse_prompt_directory_path,
                expected_file_name="clarity_coherence_prompt.txt",
            ),
            default=None,
            metavar="DIRECTORY",
            help="Directory containing clarity_coherence_prompt.txt that overrides the default prompt",
        )
        parser.add_argument(
            "--contribution-prompt",
            dest="contribution_prompt",
            type=partial(
                self._parse_prompt_directory_path,
                expected_file_name="contribution_prompt.txt",
            ),
            default=None,
            metavar="DIRECTORY",
            help="Directory containing contribution_prompt.txt that overrides the default contribution prompt",
        )
        parser.add_argument(
            "--research-lines",
            dest="research_lines",
            type=partial(
                self._parse_prompt_directory_path,
                expected_file_name="research_lines.txt",
            ),
            default=None,
            metavar="DIRECTORY",
            help="Directory containing research_lines.txt that overrides the default research lines",
        )
        return parser

    def _parse_boolean_text(self, text: str) -> bool:
        """Convert a case-insensitive "true" or "false" into a boolean."""
        normalized_text = text.lower()
        if normalized_text not in self.BOOLEAN_VALUES_BY_TEXT:
            raise ArgumentTypeError(f"Valor no válido: '{text}'. Use true o false.")
        return self.BOOLEAN_VALUES_BY_TEXT[normalized_text]

    def _parse_prompts_directory_path(self, text: str) -> Path:
        """Validate that the directory exists and contains every file of a complete prompt set."""
        directory_path = Path(text)
        if not directory_path.is_dir():
            raise ArgumentTypeError(f"El directorio no existe o no es un directorio: '{text}'.")
        for relative_path in CommandLineArguments.prompt_root_relative_paths():
            if not (directory_path / relative_path).is_file():
                missing_file_name = relative_path.as_posix()
                raise ArgumentTypeError(
                    f"No se encontró el archivo '{missing_file_name}' en el directorio: '{text}'."
                )
        return directory_path

    def _parse_prompt_directory_path(self, text: str, expected_file_name: str) -> Path:
        """Validate that the directory exists and contains the expected prompt file."""
        directory_path = Path(text)
        if not directory_path.is_dir():
            raise ArgumentTypeError(f"El directorio no existe o no es un directorio: '{text}'.")
        file_path = directory_path / expected_file_name
        if not file_path.is_file():
            raise ArgumentTypeError(
                f"No se encontró el archivo '{expected_file_name}' en el directorio: '{text}'."
            )
        return directory_path
