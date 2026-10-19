"""
batch-main.py
Command line entry point for the batch analysis of Silvina Editorial Assistant.
Runs every document of every run listed in a TOML batch file.
"""

# ruff: noqa: E402 — sys.path must be extended with the project root before
# the src.* imports below can resolve.

from io import TextIOWrapper
from pathlib import Path
from sys import exit, path, stderr, stdout

if isinstance(stdout, TextIOWrapper):
    stdout.reconfigure(encoding="utf-8", errors="replace")
if isinstance(stderr, TextIOWrapper):
    stderr.reconfigure(encoding="utf-8", errors="replace")

project_root = Path(__file__).parent
path.insert(0, str(project_root))

from src.infrastructure.cli.batch_command_line_argument_parser import (
    BatchCommandLineArgumentParser,
)
from src.infrastructure.env_config import EnvConfig
from src.infrastructure.wirings.batch_command_wiring import BatchCommandWiring
from src.infrastructure.wirings.logging_config_wiring import LoggingConfigWiring


def main():
    """Configure logging, run the batch file and exit when it does not succeed."""
    LoggingConfigWiring().create_logging_config().configure()
    print("\n" + "=" * 80)
    print(f"   SILVINA EDITORIAL ASSISTANT v{EnvConfig().silvina_version}")
    print("   Análisis por lotes")
    print("=" * 80 + "\n")

    batch_file_path = BatchCommandLineArgumentParser().parse()
    exit_status = BatchCommandWiring().create_command().run(batch_file_path)
    if exit_status != 0:
        exit(exit_status)


if __name__ == "__main__":
    main()
