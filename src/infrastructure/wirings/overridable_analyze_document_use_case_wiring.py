from collections.abc import Mapping

from src.infrastructure.env_config import EnvConfig
from src.infrastructure.overridable_env_config import OverridableEnvConfig
from src.infrastructure.wirings.analyze_document_use_case_wiring import (
    AnalyzeDocumentUseCaseWiring,
)


class OverridableAnalyzeDocumentUseCaseWiring(AnalyzeDocumentUseCaseWiring):
    """Analysis composition root whose whole pipeline uses environment overrides."""

    def __init__(self, environment_overrides: Mapping[str, str | None]) -> None:
        """Keep the overrides applied to the configuration built for the pipeline."""
        super().__init__()
        self._environment_overrides = dict(environment_overrides)

    def get_active_model_name(self) -> str:
        """Return the effective model name with the overrides applied."""
        return self._get_active_model_name()

    def _get_env_config(self) -> EnvConfig:
        if self._env_config_instance is None:
            self._env_config_instance = OverridableEnvConfig(self._environment_overrides)
        return self._env_config_instance
