from dataclasses import dataclass

from src.infrastructure.cli.command_line_arguments import CommandLineArguments


@dataclass(frozen=True)
class BatchRun:
    """One model or parameter configuration of a batch and the documents it analyzes."""

    name: str
    document_arguments: tuple[CommandLineArguments, ...]
