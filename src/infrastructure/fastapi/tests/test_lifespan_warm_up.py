from os import environ
from unittest import TestCase
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from src.domain.exceptions.language_model_errors import LanguageModelNotFound
from src.infrastructure.fastapi.fastapi_app import _warm_up_language_model, create_app


class TestLifespanWarmUp(TestCase):
    """Unit tests for FastAPI lifespan language model warmup execution and error handling."""

    @patch("src.infrastructure.fastapi.fastapi_app.threading.Thread")
    @patch("src.infrastructure.fastapi.fastapi_app.get_warm_up_language_model_use_case")
    def test_lifespan_starts_daemon_thread_when_warmup_enabled_and_testing_unset(
        self,
        mock_get_use_case: MagicMock,
        mock_thread_class: MagicMock,
    ) -> None:
        mock_use_case = MagicMock()
        mock_get_use_case.return_value = mock_use_case
        mock_thread_instance = MagicMock()
        mock_thread_class.return_value = mock_thread_instance

        with patch.dict(environ):
            environ.pop("TESTING", None)
            application = create_app(
                auto_open_browser=False,
                warm_up_language_model=True,
            )
            with TestClient(application):
                pass

        mock_thread_class.assert_called_once_with(
            target=_warm_up_language_model,
            args=(mock_use_case,),
            daemon=True,
        )
        mock_thread_instance.start.assert_called_once_with()

    @patch("src.infrastructure.fastapi.fastapi_app.threading.Thread")
    @patch("src.infrastructure.fastapi.fastapi_app.get_warm_up_language_model_use_case")
    def test_lifespan_does_not_start_thread_when_warmup_disabled(
        self,
        mock_get_use_case: MagicMock,
        mock_thread_class: MagicMock,
    ) -> None:
        with patch.dict(environ):
            environ.pop("TESTING", None)
            application = create_app(
                auto_open_browser=False,
                warm_up_language_model=False,
            )
            with TestClient(application):
                pass

        mock_thread_class.assert_not_called()
        mock_get_use_case.assert_not_called()

    @patch("src.infrastructure.fastapi.fastapi_app.threading.Thread")
    @patch("src.infrastructure.fastapi.fastapi_app.get_warm_up_language_model_use_case")
    def test_lifespan_does_not_start_thread_when_testing_environment_variable_is_set(
        self,
        mock_get_use_case: MagicMock,
        mock_thread_class: MagicMock,
    ) -> None:
        with patch.dict(environ, {"TESTING": "True"}):
            application = create_app(
                auto_open_browser=False,
                warm_up_language_model=True,
            )
            with TestClient(application):
                pass

        mock_thread_class.assert_not_called()
        mock_get_use_case.assert_not_called()

    def test_warm_up_language_model_logs_warning_on_domain_error(self) -> None:
        mock_warm_up_use_case = MagicMock()
        mock_warm_up_use_case.execute.side_effect = LanguageModelNotFound()

        with self.assertLogs(
            "src.infrastructure.fastapi.fastapi_app", level="WARNING"
        ) as captured_logs:
            _warm_up_language_model(mock_warm_up_use_case)

        self.assertEqual(len(captured_logs.output), 1)
        self.assertIn("Language model warmup failed", captured_logs.output[0])
        self.assertIn(LanguageModelNotFound.MESSAGE, captured_logs.output[0])

    def test_warm_up_language_model_logs_warning_on_unexpected_exception(self) -> None:
        mock_warm_up_use_case = MagicMock()
        mock_warm_up_use_case.execute.side_effect = RuntimeError("Ollama connection broke")

        with self.assertLogs(
            "src.infrastructure.fastapi.fastapi_app", level="WARNING"
        ) as captured_logs:
            _warm_up_language_model(mock_warm_up_use_case)

        self.assertEqual(len(captured_logs.output), 1)
        self.assertIn("Ollama connection broke", captured_logs.output[0])

    def test_warm_up_language_model_logs_no_warning_on_success(self) -> None:
        mock_warm_up_use_case = MagicMock()

        with self.assertNoLogs("src.infrastructure.fastapi.fastapi_app", level="WARNING"):
            _warm_up_language_model(mock_warm_up_use_case)

        mock_warm_up_use_case.execute.assert_called_once_with()
