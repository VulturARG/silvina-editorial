from atexit import register
from logging import FileHandler, Logger, getLogger
from os import environ
from os.path import join, normcase, realpath
from pathlib import Path
from tempfile import TemporaryDirectory

from src.infrastructure.tests.test_doubles.complete_test_environment import (
    CompleteTestEnvironment,
)


class IsolatedTestEnvironment:
    """Provides isolated filesystem paths and environment variables for test execution."""

    _temporary_directory: TemporaryDirectory[str] | None = None

    @classmethod
    def apply(cls) -> None:
        """Apply test environment isolation settings to os.environ."""
        if cls._temporary_directory is None:
            cls._temporary_directory = TemporaryDirectory(
                prefix="silvina-test-",
                ignore_cleanup_errors=True,
            )
            register(cls.release)
        temporary_directory_path = cls._temporary_directory.name
        environ.update(CompleteTestEnvironment.application_variables())
        environ["TESTING"] = "True"
        environ["METRICS_DATABASE_PATH"] = join(temporary_directory_path, "metrics.db")
        environ["LOG_FILE_PATH"] = join(temporary_directory_path, "silvina.log")
        environ["USE_EXTERNAL_LLM"] = "false"

    @classmethod
    def release(cls) -> None:
        """Release temporary directory resources and detach open file handlers."""
        if cls._temporary_directory is None:
            return
        temporary_directory_path = cls._temporary_directory.name
        cls._close_and_detach_handlers(temporary_directory_path)
        cls._temporary_directory.cleanup()
        cls._temporary_directory = None

    @classmethod
    def _close_and_detach_handlers(cls, temporary_directory_path: str) -> None:
        loggers: list[Logger] = [getLogger()]
        for named_logger in list(getLogger().manager.loggerDict.values()):
            if isinstance(named_logger, Logger):
                loggers.append(named_logger)

        for logger in loggers:
            for handler in list(logger.handlers):
                if isinstance(handler, FileHandler) and handler.baseFilename:
                    if cls._is_path_inside_directory(
                        handler.baseFilename, temporary_directory_path
                    ):
                        handler.close()
                        logger.removeHandler(handler)

    @staticmethod
    def _is_path_inside_directory(file_path: str, directory_path: str) -> bool:
        resolved_file_path = Path(normcase(realpath(file_path)))
        resolved_directory_path = Path(normcase(realpath(directory_path)))
        return resolved_file_path.is_relative_to(resolved_directory_path)
