from unittest import TestCase
from unittest.mock import Mock, patch

import web_main
from src.infrastructure.fastapi.fastapi_app import app as expected_app


class TestWebMainLogging(TestCase):
    """Test suite verifying logging initialization in web_main entry point."""

    @patch("web_main.LanguageModelWarmUpStarter")
    @patch("web_main.uvicorn.run")
    @patch("web_main.LoggingConfigWiring")
    def test_main_configures_logging_before_running_uvicorn(
        self,
        mock_logging_config_wiring_class,
        mock_uvicorn_run,
        mock_language_model_warm_up_starter_class,
    ) -> None:
        execution_order = []
        mock_logging_config_wiring_class.return_value.create_logging_config.return_value.configure.side_effect = (
            lambda: execution_order.append("configure_logging")
        )
        mock_uvicorn_run.side_effect = lambda *args, **kwargs: execution_order.append("uvicorn_run")

        web_main.main()

        mock_logging_config_wiring_class.return_value.create_logging_config.return_value.configure.assert_called_once()
        mock_uvicorn_run.assert_called_once_with(expected_app, host="127.0.0.1", port=7861)
        self.assertEqual(execution_order, ["configure_logging", "uvicorn_run"])

    @patch("web_main.LanguageModelWarmUpStarter")
    @patch("web_main.uvicorn.run")
    @patch("web_main.LoggingConfigWiring")
    def test_main_ordering_with_mock_parent(
        self,
        mock_logging_config_wiring_class,
        mock_uvicorn_run,
        mock_language_model_warm_up_starter_class,
    ) -> None:
        manager = Mock()
        manager.attach_mock(mock_logging_config_wiring_class, "LoggingConfigWiring")
        manager.attach_mock(mock_uvicorn_run, "uvicorn_run")

        web_main.main()

        call_names = [call[0] for call in manager.mock_calls]
        configure_index = call_names.index(
            "LoggingConfigWiring().create_logging_config().configure"
        )
        uvicorn_index = call_names.index("uvicorn_run")
        self.assertLess(configure_index, uvicorn_index)

    @patch("web_main.LanguageModelWarmUpStarter")
    @patch("web_main.uvicorn.run")
    @patch("web_main.LoggingConfigWiring")
    def test_main_starts_warm_up_after_logging_and_before_uvicorn_execution_order(
        self,
        mock_logging_config_wiring_class,
        mock_uvicorn_run,
        mock_language_model_warm_up_starter_class,
    ) -> None:
        execution_order = []
        mock_logging_config_wiring_class.return_value.create_logging_config.return_value.configure.side_effect = (
            lambda: execution_order.append("configure_logging")
        )
        mock_language_model_warm_up_starter_class.return_value.start.side_effect = lambda: (
            execution_order.append("warm_up_start")
        )
        mock_uvicorn_run.side_effect = lambda *args, **kwargs: execution_order.append("uvicorn_run")

        web_main.main()

        mock_language_model_warm_up_starter_class.return_value.start.assert_called_once_with()
        self.assertEqual(
            execution_order,
            ["configure_logging", "warm_up_start", "uvicorn_run"],
        )

    @patch("web_main.LanguageModelWarmUpStarter")
    @patch("web_main.uvicorn.run")
    @patch("web_main.LoggingConfigWiring")
    def test_main_starts_warm_up_ordering_with_mock_parent(
        self,
        mock_logging_config_wiring_class,
        mock_uvicorn_run,
        mock_language_model_warm_up_starter_class,
    ) -> None:
        manager = Mock()
        manager.attach_mock(mock_logging_config_wiring_class, "LoggingConfigWiring")
        manager.attach_mock(mock_language_model_warm_up_starter_class, "LanguageModelWarmUpStarter")
        manager.attach_mock(mock_uvicorn_run, "uvicorn_run")

        web_main.main()

        mock_language_model_warm_up_starter_class.return_value.start.assert_called_once_with()
        call_names = [call[0] for call in manager.mock_calls]
        configure_index = call_names.index(
            "LoggingConfigWiring().create_logging_config().configure"
        )
        warmup_index = call_names.index("LanguageModelWarmUpStarter().start")
        uvicorn_index = call_names.index("uvicorn_run")
        self.assertLess(configure_index, warmup_index)
        self.assertLess(warmup_index, uvicorn_index)
