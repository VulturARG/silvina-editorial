from os import environ
from unittest import TestCase
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from src.infrastructure.fastapi.fastapi_app import _open_browser, app, create_app


class TestLifespanBackgroundThreads(TestCase):
    @patch("src.application.warm_up_language_model_use_case.WarmUpLanguageModelUseCase.execute")
    @patch("src.infrastructure.fastapi.fastapi_app.threading.Thread")
    def test_production_app_lifespan_only_starts_browser_thread(
        self,
        mock_thread_class: MagicMock,
        mock_warm_up_execute: MagicMock,
    ) -> None:
        with patch.dict(environ):
            environ.pop("TESTING", None)
            with TestClient(app):
                pass

        self.assertGreater(mock_thread_class.call_count, 0)
        for thread_call in mock_thread_class.call_args_list:
            self.assertIs(thread_call.kwargs.get("target"), _open_browser)
        mock_warm_up_execute.assert_not_called()

    @patch("src.application.warm_up_language_model_use_case.WarmUpLanguageModelUseCase.execute")
    @patch("src.infrastructure.fastapi.fastapi_app.threading.Thread")
    def test_lifespan_starts_no_thread_when_auto_open_browser_disabled(
        self,
        mock_thread_class: MagicMock,
        mock_warm_up_execute: MagicMock,
    ) -> None:
        with patch.dict(environ):
            environ.pop("TESTING", None)
            application = create_app(auto_open_browser=False)
            with TestClient(application):
                pass

        mock_thread_class.assert_not_called()
        mock_warm_up_execute.assert_not_called()
