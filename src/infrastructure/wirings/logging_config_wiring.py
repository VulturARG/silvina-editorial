from dotenv import load_dotenv

from src.domain.metrics.analysis_context_port import AnalysisContextPort
from src.infrastructure.adapters.metrics.analysis_context_adapter import (
    AnalysisContextAdapter,
)
from src.infrastructure.config.logging_config import LoggingConfig
from src.infrastructure.env_config import EnvConfig

load_dotenv()


class LoggingConfigWiring:
    """Factory for assembling centralized logging configuration."""

    def create_logging_config(self) -> LoggingConfig:
        """Build a ready-to-configure LoggingConfig instance from environment settings."""
        environment_config = self._get_env_config()
        return LoggingConfig(
            log_file_path=environment_config.log_file_path,
            log_level=environment_config.log_level,
            backup_count=environment_config.log_retention_days,
            analysis_context_port=self._get_analysis_context_port(),
        )

    def _get_env_config(self) -> EnvConfig:
        return EnvConfig()

    def _get_analysis_context_port(self) -> AnalysisContextPort:
        return AnalysisContextAdapter()
