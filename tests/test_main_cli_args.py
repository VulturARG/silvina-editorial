"""
Unit tests for the main() entry point of main.py: banner and exit statuses.
"""

from contextlib import redirect_stdout
from io import StringIO
from os import environ
from os.path import dirname, join
from sys import path
from unittest import TestCase, main
from unittest.mock import patch

path.insert(0, join(dirname(__file__), ".."))

from main import main as run_main
from src.infrastructure.cli.command_line_arguments import CommandLineArguments

FIXTURE_DOCUMENT_PATH = join(
    dirname(__file__),
    "fixtures",
    "capacidades_razonamiento_emergente_LLMs.docx",
)


class TestMainBanner(TestCase):
    def test_banner_shows_the_configured_version(self):
        captured_output = StringIO()
        with patch.dict(environ, {"TESTING": "True", "SILVINA_VERSION": "7.7.7"}):
            with patch("sys.argv", ["main.py", "nonexistent_document_xyz.docx"]):
                with redirect_stdout(captured_output):
                    with self.assertRaises(SystemExit):
                        run_main()
        self.assertIn("v7.7.7", captured_output.getvalue())


class TestMainExitStatuses(TestCase):
    def test_exits_2_and_explains_when_document_does_not_exist(self):
        captured_output = StringIO()
        with patch("sys.argv", ["main.py", "nonexistent_document_xyz.docx"]):
            with redirect_stdout(captured_output):
                with self.assertRaises(SystemExit) as context:
                    run_main()
        self.assertEqual(context.exception.code, 2)
        self.assertIn("El documento no existe", captured_output.getvalue())

    def test_exits_2_and_explains_when_document_is_not_docx(self):
        captured_output = StringIO()
        with patch("sys.argv", ["main.py", __file__]):
            with redirect_stdout(captured_output):
                with self.assertRaises(SystemExit) as context:
                    run_main()
        self.assertEqual(context.exception.code, 2)
        self.assertIn("El documento debe ser un archivo Word (.docx)", captured_output.getvalue())

    def test_exits_with_the_command_status_when_the_analysis_fails(self):
        with patch("sys.argv", ["main.py", FIXTURE_DOCUMENT_PATH]):
            with patch("main.DocumentAnalysisCommandWiring") as mock_wiring_class:
                mock_wiring_class.return_value.create_command.return_value.run.return_value = 1
                with self.assertRaises(SystemExit) as context:
                    run_main()
        self.assertEqual(context.exception.code, 1)

    def test_returns_normally_when_the_command_succeeds(self):
        with patch("sys.argv", ["main.py", FIXTURE_DOCUMENT_PATH]):
            with patch("main.DocumentAnalysisCommandWiring") as mock_wiring_class:
                run_command = mock_wiring_class.return_value.create_command.return_value.run
                run_command.return_value = 0
                with redirect_stdout(StringIO()):
                    run_main()
        run_command.assert_called_once()
        arguments = run_command.call_args.args[0]
        self.assertIsInstance(arguments, CommandLineArguments)
        self.assertEqual(arguments.document_name, FIXTURE_DOCUMENT_PATH)


if __name__ == "__main__":
    main()
