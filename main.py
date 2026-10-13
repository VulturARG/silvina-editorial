"""
main.py
Command line entry point for Silvina Editorial Assistant.
Analyzes a Word document and saves its Word, JSON and HTML reports.
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

# Add project root to path
project_root = Path(__file__).parent
path.insert(0, str(project_root))

from src.infrastructure.cli.command_line_argument_parser import CommandLineArgumentParser
from src.infrastructure.env_config import EnvConfig
from src.infrastructure.wirings.document_analysis_command_wiring import (
    DocumentAnalysisCommandWiring,
)
from src.infrastructure.wirings.logging_config_wiring import LoggingConfigWiring


def main():
    """Configure logging, run the document analysis command and exit when it does not succeed."""
    LoggingConfigWiring().create_logging_config().configure()
    print("\n" + "=" * 80)
    print(f"   SILVINA EDITORIAL ASSISTANT v{EnvConfig().silvina_version}")
    print("   Asistente de Análisis Editorial para Documentos Académicos")
    print("=" * 80 + "\n")

    arguments = CommandLineArgumentParser().parse()
    exit_status = DocumentAnalysisCommandWiring().create_command().run(arguments)
    if exit_status != 0:
        exit(exit_status)


if __name__ == "__main__":
    main()
