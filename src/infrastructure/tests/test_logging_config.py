from logging import getLogger
from logging.handlers import TimedRotatingFileHandler
from os.path import abspath
from pathlib import Path
from re import match
from tempfile import TemporaryDirectory
from unittest import TestCase

from src.domain.tests.metrics.fake_analysis_context_port import FakeAnalysisContextPort
from src.infrastructure.config.logging_config import LoggingConfig


class TestLoggingConfig(TestCase):
    def setUp(self) -> None:
        self._root_logger = getLogger()
        self._initial_root_handlers = list(self._root_logger.handlers)
        self._initial_root_level = self._root_logger.level
        self._temporary_directory = TemporaryDirectory()
        self._log_file_path = str(
            Path(self._temporary_directory.name) / "nested_logs" / "silvina.log"
        )
        self._fake_analysis_context_port = FakeAnalysisContextPort()
        self._logger = getLogger("test_logging_config")
        self._logger.setLevel(0)

    def tearDown(self) -> None:
        for handler in list(self._root_logger.handlers):
            if handler not in self._initial_root_handlers:
                self._root_logger.removeHandler(handler)
                handler.close()
        for handler in self._initial_root_handlers:
            if handler not in self._root_logger.handlers:
                self._root_logger.addHandler(handler)
        self._root_logger.setLevel(self._initial_root_level)
        self._temporary_directory.cleanup()

    def _flush_handlers(self) -> None:
        for handler in self._root_logger.handlers:
            handler.flush()

    def _read_log_file(self) -> str:
        self._flush_handlers()
        return Path(self._log_file_path).read_text(encoding="utf-8")

    def test_creates_missing_parent_folders_and_log_file_after_logging(self) -> None:
        self.assertFalse(Path(self._log_file_path).parent.exists())

        logging_config = LoggingConfig(
            log_file_path=self._log_file_path,
            log_level="INFO",
            backup_count=3,
            analysis_context_port=self._fake_analysis_context_port,
        )
        logging_config.configure()

        self.assertTrue(Path(self._log_file_path).parent.exists())

        self._logger.info("application started")
        content = self._read_log_file()

        self.assertTrue(Path(self._log_file_path).exists())
        self.assertIn("application started", content)

    def test_written_line_contains_iso_timestamp_with_timezone_offset(self) -> None:
        self._fake_analysis_context_port.set_analysis_id("analysis-123")
        logging_config = LoggingConfig(
            log_file_path=self._log_file_path,
            log_level="INFO",
            backup_count=3,
            analysis_context_port=self._fake_analysis_context_port,
        )
        logging_config.configure()

        self._logger.info("hello")
        content = self._read_log_file()

        expected_pattern = (
            r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{4} \| INFO \| "
            r"test_logging_config \| analysis_id=analysis-123 \| hello$"
        )
        first_line = content.strip().splitlines()[0]
        self.assertIsNotNone(match(expected_pattern, first_line))

    def test_uses_dash_placeholder_when_no_analysis_is_active(self) -> None:
        logging_config = LoggingConfig(
            log_file_path=self._log_file_path,
            log_level="INFO",
            backup_count=3,
            analysis_context_port=self._fake_analysis_context_port,
        )
        logging_config.configure()

        self._logger.info("hello")
        content = self._read_log_file()

        expected_pattern = (
            r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{4} \| INFO \| "
            r"test_logging_config \| analysis_id=- \| hello$"
        )
        first_line = content.strip().splitlines()[0]
        self.assertIsNotNone(match(expected_pattern, first_line))

    def test_level_filtering_ignores_debug_and_writes_warning_when_level_is_info(
        self,
    ) -> None:
        logging_config = LoggingConfig(
            log_file_path=self._log_file_path,
            log_level="INFO",
            backup_count=3,
            analysis_context_port=self._fake_analysis_context_port,
        )
        logging_config.configure()

        self._logger.debug("debug message that should be ignored")
        self._logger.warning("warning message that should be written")
        content = self._read_log_file()

        self.assertNotIn("debug message that should be ignored", content)
        self.assertIn("warning message that should be written", content)

    def test_handler_is_timed_rotating_file_handler_with_configured_properties(
        self,
    ) -> None:
        logging_config = LoggingConfig(
            log_file_path=self._log_file_path,
            log_level="INFO",
            backup_count=5,
            analysis_context_port=self._fake_analysis_context_port,
        )
        logging_config.configure()

        matching_handlers = [
            handler
            for handler in self._root_logger.handlers
            if isinstance(handler, TimedRotatingFileHandler)
            and handler.baseFilename == abspath(self._log_file_path)
        ]
        self.assertEqual(len(matching_handlers), 1)
        handler = matching_handlers[0]
        self.assertEqual(handler.backupCount, 5)
        self.assertEqual(handler.when, "MIDNIGHT")
        self.assertEqual(handler.encoding, "utf-8")

    def test_calling_configure_twice_produces_exactly_one_handler_and_one_line_per_message(
        self,
    ) -> None:
        logging_config = LoggingConfig(
            log_file_path=self._log_file_path,
            log_level="INFO",
            backup_count=3,
            analysis_context_port=self._fake_analysis_context_port,
        )
        logging_config.configure()
        logging_config.configure()

        matching_handlers = [
            handler
            for handler in self._root_logger.handlers
            if isinstance(handler, TimedRotatingFileHandler)
            and handler.baseFilename == abspath(self._log_file_path)
        ]
        self.assertEqual(len(matching_handlers), 1)

        self._logger.info("unique message")
        content = self._read_log_file()
        matching_lines = [line for line in content.splitlines() if "unique message" in line]
        self.assertEqual(len(matching_lines), 1)

    def test_unicode_and_multiline_messages_are_written(self) -> None:
        logging_config = LoggingConfig(
            log_file_path=self._log_file_path,
            log_level="INFO",
            backup_count=3,
            analysis_context_port=self._fake_analysis_context_port,
        )
        logging_config.configure()

        multiline_message = "Primera línea con acento: áéíóú ñ 日本語 🚀\nSegunda línea de texto"
        self._logger.info(multiline_message)
        content = self._read_log_file()

        self.assertIn("Primera línea con acento: áéíóú ñ 日本語 🚀", content)
        self.assertIn("Segunda línea de texto", content)

    def test_invalid_level_raises_and_leaves_no_new_handler_attached_to_root_logger(
        self,
    ) -> None:
        logging_config = LoggingConfig(
            log_file_path=self._log_file_path,
            log_level="LOUD",
            backup_count=3,
            analysis_context_port=self._fake_analysis_context_port,
        )
        handlers_before = list(self._root_logger.handlers)

        with self.assertRaises(ValueError):
            logging_config.configure()

        self.assertEqual(self._root_logger.handlers, handlers_before)
