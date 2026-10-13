from argparse import ArgumentParser, ArgumentTypeError
from collections.abc import Sequence
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
        return parser

    def _parse_boolean_text(self, text: str) -> bool:
        """Convert a case-insensitive "true" or "false" into a boolean."""
        normalized_text = text.lower()
        if normalized_text not in self.BOOLEAN_VALUES_BY_TEXT:
            raise ArgumentTypeError(f"Valor no válido: '{text}'. Use true o false.")
        return self.BOOLEAN_VALUES_BY_TEXT[normalized_text]
