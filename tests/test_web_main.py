"""Unit tests for root launcher web_main.py and launch_silvina.bat script."""

from pathlib import Path
import runpy
from unittest import TestCase
from unittest.mock import patch

from src.infrastructure.fastapi.fastapi_app import app as expected_app
import web_main


class TestWebMain(TestCase):
    """Test suite for web_main.py root launcher and batch file configuration."""

    def test_web_main_exposes_fastapi_app(self) -> None:
        """Verify web_main exposes the assembled FastAPI application instance."""
        self.assertIs(web_main.app, expected_app)

    @patch("web_main.LanguageModelWarmUpStarter")
    @patch("web_main.uvicorn.run")
    def test_main_runs_uvicorn_with_expected_host_and_port(
        self,
        mock_run,
        mock_warm_up_starter,
    ) -> None:
        """Verify main() invokes uvicorn with the FastAPI app on 127.0.0.1:7861."""
        web_main.main()
        mock_run.assert_called_once_with(expected_app, host="127.0.0.1", port=7861)

    @patch(
        "src.infrastructure.fastapi.src.utils.language_model_warm_up_starter.LanguageModelWarmUpStarter.start"
    )
    @patch("uvicorn.run")
    def test_web_main_module_execution(self, mock_run, mock_warm_up_start) -> None:
        """Verify running web_main as __main__ invokes uvicorn.run."""
        runpy.run_module("web_main", run_name="__main__")
        mock_run.assert_called_once_with(expected_app, host="127.0.0.1", port=7861)

    def test_launch_silvina_bat_invokes_web_main(self) -> None:
        """Verify launch_silvina.bat runs web_main.py instead of gradio_app.py."""
        bat_path = Path(__file__).resolve().parents[1] / "launch_silvina.bat"
        self.assertTrue(bat_path.exists(), "launch_silvina.bat must exist")

        content = bat_path.read_text(encoding="utf-8", errors="ignore")
        self.assertIn("python web_main.py", content)
        self.assertNotIn("python gradio_app.py", content)
        self.assertNotIn("Gradio", content)
        self.assertIn("El servidor web local se levantara en breve.", content)
