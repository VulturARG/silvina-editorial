from logging import getLogger
from os import environ
from unittest import TestCase
from unittest.mock import patch

from src.domain.exceptions.settings_errors import SettingValueMissing
from src.domain.metrics.analysis_context_port import AnalysisContextPort
from src.infrastructure.adapters.metrics.analysis_context_adapter import (
    AnalysisContextAdapter,
)
from src.infrastructure.config.logging_config import LoggingConfig
from src.infrastructure.tests.test_doubles.complete_test_environment import (
    CompleteTestEnvironment,
)
from src.infrastructure.wirings.logging_config_wiring import LoggingConfigWiring


class TestLoggingConfigWiring(TestCase):
    @staticmethod
    def _complete_environment(overrides: dict[str, str] | None = None) -> dict[str, str]:
        environment = {
            **CompleteTestEnvironment.application_variables(),
            "METRICS_DATABASE_PATH": "/custom/path/metrics.db",
            "LOG_FILE_PATH": "/custom/path/silvina.log",
        }
        if overrides:
            environment.update(overrides)
        return environment

    def setUp(self) -> None:
        self._root_logger = getLogger()
        self._initial_root_handlers = list(self._root_logger.handlers)
        self._initial_root_level = self._root_logger.level

    def tearDown(self) -> None:
        for handler in list(self._root_logger.handlers):
            if handler not in self._initial_root_handlers:
                self._root_logger.removeHandler(handler)
                handler.close()
        for handler in self._initial_root_handlers:
            if handler not in self._root_logger.handlers:
                self._root_logger.addHandler(handler)
        self._root_logger.setLevel(self._initial_root_level)

    def test_create_logging_config_returns_logging_config_instance(self) -> None:
        wiring = LoggingConfigWiring()
        logging_config = wiring.create_logging_config()
        self.assertIsInstance(logging_config, LoggingConfig)

    def test_create_logging_config_injects_environment_values(self) -> None:
        environment_overrides = {
            "LOG_FILE_PATH": "/custom/path/application.log",
            "LOG_LEVEL": "DEBUG",
            "LOG_RETENTION_DAYS": "30",
        }
        with patch.dict(environ, environment_overrides):
            logging_config = LoggingConfigWiring().create_logging_config()

        self.assertEqual(logging_config._log_file_path, "/custom/path/application.log")
        self.assertEqual(logging_config._log_level, "DEBUG")
        self.assertEqual(logging_config._backup_count, 30)

    def test_create_logging_config_wires_analysis_context_adapter(self) -> None:
        logging_config = LoggingConfigWiring().create_logging_config()
        self.assertIsInstance(logging_config._analysis_context_port, AnalysisContextAdapter)
        self.assertIsInstance(logging_config._analysis_context_port, AnalysisContextPort)

    def test_create_logging_config_does_not_attach_handler(self) -> None:
        handlers_before = list(self._root_logger.handlers)
        LoggingConfigWiring().create_logging_config()
        self.assertEqual(self._root_logger.handlers, handlers_before)

    def test_create_logging_config_raises_setting_value_missing_when_log_file_path_is_missing(
        self,
    ) -> None:
        environment = self._complete_environment()
        del environment["LOG_FILE_PATH"]
        with patch.dict(environ, environment, clear=True):
            with self.assertRaises(SettingValueMissing) as context:
                LoggingConfigWiring().create_logging_config()
        self.assertIn("LOG_FILE_PATH", context.exception.dict()["error"])
