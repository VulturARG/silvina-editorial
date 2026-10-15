"""
E2E test for the command line document analysis flow.
Runs in-process with mocked external dependencies (Ollama, LanguageTool, COM).
"""

from contextlib import redirect_stdout
from io import StringIO
from json import loads
from os.path import abspath, dirname, exists, join
from pathlib import Path
from sys import modules, path
from tempfile import TemporaryDirectory
from unittest import TestCase, main, skipUnless
from unittest.mock import MagicMock, patch

path.insert(0, join(dirname(__file__), "..", ".."))

if "language_tool_python" not in modules:
    _mock_ltp = MagicMock()
    _mock_lt_instance = MagicMock()
    _mock_lt_instance.check.return_value = []
    _mock_ltp.LanguageTool.return_value = _mock_lt_instance
    modules["language_tool_python"] = _mock_ltp

from src.infrastructure.cli.command_line_arguments import CommandLineArguments
from src.infrastructure.cli.windows_file_name_sanitizer import WindowsFileNameSanitizer
from src.infrastructure.env_config import EnvConfig
from src.infrastructure.wirings.document_analysis_command_wiring import (
    DocumentAnalysisCommandWiring,
)

FIXTURE_PATH = abspath(
    join(dirname(__file__), "..", "fixtures", "capacidades_razonamiento_emergente_LLMs.docx")
)
FIXTURE_STEM = "capacidades_razonamiento_emergente_LLMs"
REPORT_EXTENSIONS = (".docx", ".json", ".html")


def _make_ollama_client_mock(
    response=(
        "S4: SI\nS5: SI\nS6: SI\n\n"
        "**Claridad** [Puntuación: 8/10]\nTexto claro y bien redactado.\n\n"
        "**Coherencia** [Puntuación: 8/10]\nIdeas conectadas de forma coherente.\n\n"
        "**Argumentación** [Puntuación: 8/10]\nArgumentos sólidos y bien fundamentados.\n\n"
        "**Conclusiones** [Puntuación: 8/10]\nConclusiones claras y consistentes."
    ),
):
    """Return a mock ollama.Client whose generate() satisfies both the
    classification (S4/S5/S6) and quality (per-dimension) response parsers."""
    mock_client = MagicMock()
    mock_client.generate.return_value = {"response": response}
    mock_client.list.return_value = {"models": []}
    return mock_client


@skipUnless(exists(FIXTURE_PATH), "Fixture .docx not available")
class TestDocumentAnalysisCommandE2E(TestCase):
    """
    In-process E2E test: runs the command line analysis of a real .docx fixture
    and verifies the Word, JSON and HTML reports it writes.
    """

    def setUp(self) -> None:
        temporary_directory = TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        self._output_directory = Path(temporary_directory.name)

    def test_run_returns_success_status(self):
        status = self._run_command(
            CommandLineArguments(
                document_name=FIXTURE_PATH, output_directory=self._output_directory
            )
        )
        self.assertEqual(status, 0)

    def test_writes_word_json_and_html_reports_named_after_document_and_model(self):
        self._run_command(
            CommandLineArguments(
                document_name=FIXTURE_PATH, output_directory=self._output_directory
            )
        )
        model_name = EnvConfig().ollama_model_name
        expected_names = sorted(
            self._report_path(model_name, extension).name for extension in REPORT_EXTENSIONS
        )
        self.assertEqual(
            sorted(file.name for file in self._output_directory.iterdir()), expected_names
        )

    def test_json_report_is_valid_and_contains_document_info_with_words(self):
        self._run_command(
            CommandLineArguments(
                document_name=FIXTURE_PATH, output_directory=self._output_directory
            )
        )
        report_path = self._report_path(EnvConfig().ollama_model_name, ".json")
        report = loads(report_path.read_text(encoding="utf-8"))
        self.assertIn("document_info", report)
        self.assertGreater(report["document_info"]["word_count"], 0)

    def test_html_report_is_a_standalone_page_without_scripts(self):
        self._run_command(
            CommandLineArguments(
                document_name=FIXTURE_PATH, output_directory=self._output_directory
            )
        )
        report_path = self._report_path(EnvConfig().ollama_model_name, ".html")
        html = report_path.read_text(encoding="utf-8")
        self.assertTrue(html.startswith("<!DOCTYPE html>"))
        self.assertIn("<style", html)
        self.assertNotIn("<script", html)

    def test_ollama_model_override_names_the_reports_with_the_overridden_model(self):
        status = self._run_command(
            CommandLineArguments(
                document_name=FIXTURE_PATH,
                output_directory=self._output_directory,
                ollama_model_name="override-model",
            )
        )
        self.assertEqual(status, 0)
        for extension in REPORT_EXTENSIONS:
            self.assertTrue(self._report_path("override-model", extension).is_file())

    def test_warms_up_language_model_before_analyzing_document(self):
        mock_client = _make_ollama_client_mock()
        mock_lt = MagicMock()
        mock_lt.check.return_value = []
        captured_output = StringIO()
        with (
            patch("ollama.Client", return_value=mock_client),
            patch(
                "src.infrastructure.adapters.llm_generator.ollama_server_adapter.Client",
                return_value=mock_client,
            ),
            patch(
                "src.infrastructure.adapters.document.win32com_word_count_adapter."
                "WIN32COM_AVAILABLE",
                False,
            ),
            patch(
                "src.infrastructure.adapters.grammar.language_tool_adapter.language_tool_python.LanguageTool",
                return_value=mock_lt,
            ),
            redirect_stdout(captured_output),
        ):
            status = (
                DocumentAnalysisCommandWiring()
                .create_command()
                .run(
                    CommandLineArguments(
                        document_name=FIXTURE_PATH,
                        output_directory=self._output_directory,
                        ollama_model_name="warmup-test-model",
                    )
                )
            )

        self.assertEqual(status, 0)
        output_text = captured_output.getvalue()
        self.assertIn("Verificando el servidor del modelo de lenguaje", output_text)
        self.assertIn("Precargando el modelo de lenguaje", output_text)
        mock_client.list.assert_called_once()
        warmup_calls = [
            call for call in mock_client.generate.call_args_list if call.kwargs.get("prompt") == ""
        ]
        self.assertEqual(len(warmup_calls), 1)
        self.assertEqual(warmup_calls[0].kwargs.get("model"), "warmup-test-model")

    def _run_command(self, arguments: CommandLineArguments) -> int:
        mock_client = _make_ollama_client_mock()
        mock_lt = MagicMock()
        mock_lt.check.return_value = []
        with (
            patch("ollama.Client", return_value=mock_client),
            patch(
                "src.infrastructure.adapters.llm_generator.ollama_server_adapter.Client",
                return_value=mock_client,
            ),
            patch(
                "src.infrastructure.adapters.document.win32com_word_count_adapter."
                "WIN32COM_AVAILABLE",
                False,
            ),
            patch(
                "src.infrastructure.adapters.grammar.language_tool_adapter.language_tool_python.LanguageTool",
                return_value=mock_lt,
            ),
            redirect_stdout(StringIO()),
        ):
            return DocumentAnalysisCommandWiring().create_command().run(arguments)

    def _report_path(self, model_name: str, extension: str) -> Path:
        sanitized_model_name = WindowsFileNameSanitizer().sanitize(model_name)
        return self._output_directory / f"{FIXTURE_STEM}_analisis_{sanitized_model_name}{extension}"


if __name__ == "__main__":
    main()
