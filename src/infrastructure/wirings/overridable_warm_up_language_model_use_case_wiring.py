from collections.abc import Mapping

from src.infrastructure.env_config import EnvConfig
from src.infrastructure.overridable_env_config import OverridableEnvConfig
from src.infrastructure.wirings.warm_up_language_model_use_case_wiring import (
    WarmUpLanguageModelUseCaseWiring,
)


class OverridableWarmUpLanguageModelUseCaseWiring(WarmUpLanguageModelUseCaseWiring):
    """Language model warmup composition root that uses environment overrides."""

    def __init__(self, environment_overrides: Mapping[str, str | None]) -> None:
        """Keep the environment overrides applied to the warm-up configuration."""
        super().__init__()
        self._environment_overrides = dict(environment_overrides)
        self._env_config_instance: OverridableEnvConfig | None = None

    def _env_config(self) -> EnvConfig:
        if self._env_config_instance is None:
            self._env_config_instance = OverridableEnvConfig(self._environment_overrides)
        return self._env_config_instance
