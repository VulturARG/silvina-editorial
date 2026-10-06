from logging import FileHandler, Handler, Logger, getLogger
from logging.handlers import TimedRotatingFileHandler
from os import environ
from os.path import exists
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from src.infrastructure.tests.isolated_test_environment import (
    IsolatedTestEnvironment,
)
from src.infrastructure.tests.test_doubles.complete_test_environment import (
    CompleteTestEnvironment,
)


class TestIsolatedTestEnvironment(TestCase):
    """Tests for IsolatedTestEnvironment."""

    @patch.dict(environ)
    def test_apply_replaces_database_and_log_paths_with_temporary_directory(
        self,
    ) -> None:
        repository_root_directory = Path(__file__).resolve().parents[3]
        repository_metrics_database_path = str(repository_root_directory / "data" / "metrics.db")
        repository_log_file_path = str(repository_root_directory / "logs" / "silvina.log")
        environ["METRICS_DATABASE_PATH"] = repository_metrics_database_path
        environ["LOG_FILE_PATH"] = repository_log_file_path

        IsolatedTestEnvironment.apply()

        configured_metrics_database_path = Path(environ["METRICS_DATABASE_PATH"]).resolve()
        configured_log_file_path = Path(environ["LOG_FILE_PATH"]).resolve()
        configured_temporary_directory = configured_metrics_database_path.parent

        self.assertEqual(configured_metrics_database_path.name, "metrics.db")
        self.assertEqual(configured_log_file_path.name, "silvina.log")
        self.assertEqual(
            configured_log_file_path.parent,
            configured_temporary_directory,
        )
        self.assertFalse(configured_temporary_directory.is_relative_to(repository_root_directory))

    @patch.dict(environ)
    def test_apply_forces_use_external_llm_to_false(self) -> None:
        environ["USE_EXTERNAL_LLM"] = "true"

        IsolatedTestEnvironment.apply()

        self.assertEqual(environ["USE_EXTERNAL_LLM"], "false")

    @patch.dict(environ)
    def test_apply_sets_testing_flag(self) -> None:
        environ.pop("TESTING", None)

        IsolatedTestEnvironment.apply()

        self.assertEqual(environ["TESTING"], "True")

    @patch.dict(environ, clear=True)
    def test_apply_sets_complete_application_environment_variables(self) -> None:
        IsolatedTestEnvironment.apply()

        for key, value in CompleteTestEnvironment.application_variables().items():
            self.assertEqual(environ.get(key), value)

    @patch.dict(environ)
    def test_apply_is_idempotent_reusing_same_directory(self) -> None:
        IsolatedTestEnvironment.apply()
        first_metrics_database_path = environ["METRICS_DATABASE_PATH"]
        first_log_file_path = environ["LOG_FILE_PATH"]

        IsolatedTestEnvironment.apply()
        second_metrics_database_path = environ["METRICS_DATABASE_PATH"]
        second_log_file_path = environ["LOG_FILE_PATH"]

        self.assertEqual(first_metrics_database_path, second_metrics_database_path)
        self.assertEqual(first_log_file_path, second_log_file_path)

    @patch.dict(environ)
    def test_apply_does_not_create_database_file(self) -> None:
        with patch.object(IsolatedTestEnvironment, "_temporary_directory", None):
            IsolatedTestEnvironment.apply()
            temporary_directory = IsolatedTestEnvironment._temporary_directory
            self.addCleanup(self._cleanup_temporary_directory, temporary_directory)

            metrics_database_path = environ["METRICS_DATABASE_PATH"]

            self.assertFalse(exists(metrics_database_path))
            self.assertFalse(exists(environ["LOG_FILE_PATH"]))

    @patch.dict(environ)
    def test_release_removes_temporary_directory_when_file_handler_is_open(
        self,
    ) -> None:
        with patch.object(IsolatedTestEnvironment, "_temporary_directory", None):
            IsolatedTestEnvironment.apply()
            temporary_directory = IsolatedTestEnvironment._temporary_directory
            self.addCleanup(self._cleanup_temporary_directory, temporary_directory)

            temporary_directory_path = Path(environ["LOG_FILE_PATH"]).parent
            handler = TimedRotatingFileHandler(
                filename=environ["LOG_FILE_PATH"],
                when="midnight",
                backupCount=1,
                encoding="utf-8",
            )
            root_logger = getLogger()
            root_logger.addHandler(handler)
            self.addCleanup(self._remove_handler_if_present, root_logger, handler)

            root_logger.warning("Test message to ensure file handle is open")

            IsolatedTestEnvironment.release()

            self.assertFalse(temporary_directory_path.exists())
            self.assertNotIn(handler, root_logger.handlers)

    @patch.dict(environ)
    def test_release_leaves_external_file_handlers_untouched(self) -> None:
        outside_temporary_directory = TemporaryDirectory()
        self.addCleanup(outside_temporary_directory.cleanup)

        outside_log_file_path = Path(outside_temporary_directory.name) / "outside.log"
        external_handler = FileHandler(
            filename=str(outside_log_file_path),
            encoding="utf-8",
        )
        root_logger = getLogger()
        root_logger.addHandler(external_handler)
        self.addCleanup(self._remove_handler_if_present, root_logger, external_handler)

        named_logger = getLogger("test_external_named_logger")
        named_external_handler = FileHandler(
            filename=str(Path(outside_temporary_directory.name) / "named_outside.log"),
            encoding="utf-8",
        )
        named_logger.addHandler(named_external_handler)
        self.addCleanup(self._remove_handler_if_present, named_logger, named_external_handler)

        with patch.object(IsolatedTestEnvironment, "_temporary_directory", None):
            IsolatedTestEnvironment.apply()
            temporary_directory = IsolatedTestEnvironment._temporary_directory
            self.addCleanup(self._cleanup_temporary_directory, temporary_directory)

            internal_handler = TimedRotatingFileHandler(
                filename=environ["LOG_FILE_PATH"],
                when="midnight",
                backupCount=1,
                encoding="utf-8",
            )
            root_logger.addHandler(internal_handler)
            self.addCleanup(self._remove_handler_if_present, root_logger, internal_handler)

            internal_named_handler = FileHandler(
                filename=str(Path(environ["LOG_FILE_PATH"]).parent / "named_internal.log"),
                encoding="utf-8",
            )
            named_logger.addHandler(internal_named_handler)
            self.addCleanup(self._remove_handler_if_present, named_logger, internal_named_handler)

            IsolatedTestEnvironment.release()

            self.assertIn(external_handler, root_logger.handlers)
            self.assertNotIn(internal_handler, root_logger.handlers)
            self.assertIn(named_external_handler, named_logger.handlers)
            self.assertNotIn(internal_named_handler, named_logger.handlers)

    @patch.dict(environ)
    def test_release_is_idempotent_and_does_nothing_without_apply(self) -> None:
        with patch.object(IsolatedTestEnvironment, "_temporary_directory", None):
            IsolatedTestEnvironment.release()
            self.assertIsNone(IsolatedTestEnvironment._temporary_directory)

            IsolatedTestEnvironment.release()
            self.assertIsNone(IsolatedTestEnvironment._temporary_directory)

    @patch.dict(environ)
    def test_release_is_idempotent_after_apply(self) -> None:
        with patch.object(IsolatedTestEnvironment, "_temporary_directory", None):
            IsolatedTestEnvironment.apply()
            IsolatedTestEnvironment.release()
            self.assertIsNone(IsolatedTestEnvironment._temporary_directory)

            IsolatedTestEnvironment.release()
            self.assertIsNone(IsolatedTestEnvironment._temporary_directory)

    @patch.dict(environ)
    def test_apply_registers_exit_callback_exactly_once(self) -> None:
        with (
            patch.object(IsolatedTestEnvironment, "_temporary_directory", None),
            patch("src.infrastructure.tests.isolated_test_environment.register") as mock_register,
        ):
            IsolatedTestEnvironment.apply()
            temporary_directory = IsolatedTestEnvironment._temporary_directory
            self.addCleanup(self._cleanup_temporary_directory, temporary_directory)

            IsolatedTestEnvironment.apply()

            mock_register.assert_called_once_with(IsolatedTestEnvironment.release)

    def _remove_handler_if_present(
        self,
        logger: Logger,
        handler: Handler,
    ) -> None:
        if handler in logger.handlers:
            logger.removeHandler(handler)
        handler.close()

    def _cleanup_temporary_directory(
        self,
        temporary_directory: TemporaryDirectory[str] | None,
    ) -> None:
        if temporary_directory is not None:
            temporary_directory.cleanup()
