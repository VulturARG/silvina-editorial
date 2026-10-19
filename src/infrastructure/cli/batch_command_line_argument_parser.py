from argparse import ArgumentParser
from collections.abc import Sequence
from pathlib import Path


class BatchCommandLineArgumentParser:
    """Parse the command line of the batch analysis into the path of the batch file."""

    def parse(self, argument_list: Sequence[str] | None = None) -> Path:
        """Parse the given arguments, or the process arguments when none are given."""
        namespace = self._build_argument_parser().parse_args(argument_list)
        return namespace.batch_file

    def _build_argument_parser(self) -> ArgumentParser:
        """Build the parser that declares the batch file positional argument."""
        parser = ArgumentParser(description="Silvina Editorial Assistant - Batch analysis")
        parser.add_argument(
            "batch_file",
            type=Path,
            help="Path of the TOML batch file that lists the runs and their documents",
        )
        return parser
