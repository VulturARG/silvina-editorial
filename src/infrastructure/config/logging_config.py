from logging import Formatter, Logger, getLogger
from logging.handlers import TimedRotatingFileHandler
from os.path import abspath
from pathlib import Path

from src.domain.metrics.analysis_context_port import AnalysisContextPort
from src.infrastructure.config.analysis_context_log_filter import (
    AnalysisContextLogFilter,
)

_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | analysis_id=%(analysis_id)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


class LoggingConfig:
    """Configures centralized timed rotating file logging with an analysis context filter."""

    def __init__(
        self,
        log_file_path: str,
        log_level: str,
        backup_count: int,
        analysis_context_port: AnalysisContextPort,
    ) -> None:
        """Initialize the logging configuration with file path, level, backup count, and context port."""
        self._log_file_path = log_file_path
        self._log_level = log_level
        self._backup_count = backup_count
        self._analysis_context_port = analysis_context_port

    def configure(self) -> None:
        """Configure the root logger with a rotating file handler and analysis context filter."""
        root_logger = getLogger()
        root_logger.setLevel(self._log_level)
        self._ensure_parent_directory()
        self._remove_existing_handler(root_logger)
        handler = self._build_handler()
        root_logger.addHandler(handler)

    def _ensure_parent_directory(self) -> None:
        Path(self._log_file_path).parent.mkdir(parents=True, exist_ok=True)

    def _remove_existing_handler(self, root_logger: Logger) -> None:
        target_path = abspath(self._log_file_path)
        for handler in list(root_logger.handlers):
            if (
                isinstance(handler, TimedRotatingFileHandler)
                and handler.baseFilename == target_path
            ):
                root_logger.removeHandler(handler)
                handler.close()

    def _build_handler(self) -> TimedRotatingFileHandler:
        handler = TimedRotatingFileHandler(
            filename=self._log_file_path,
            when="midnight",
            backupCount=self._backup_count,
            encoding="utf-8",
        )
        formatter = Formatter(fmt=_LOG_FORMAT, datefmt=_DATE_FORMAT)
        handler.setFormatter(formatter)
        handler.addFilter(AnalysisContextLogFilter(self._analysis_context_port))
        return handler
