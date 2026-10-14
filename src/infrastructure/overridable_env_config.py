from collections.abc import Mapping
from os import environ
from pathlib import Path

from src.infrastructure.env_config import EnvConfig
from src.infrastructure.resources.project import SETTINGS_FILE_PATH


class OverridableEnvConfig(EnvConfig):
    """Environment configuration with temporary, per-instance environment overrides.

    Overrides such as OLLAMA_MODEL_NAME, USE_EXTERNAL_LLM, LLM_PROVIDER,
    EXTERNAL_LLM_MODEL_NAME or APP_MODE are written to the process environment only
    while EnvConfig is being built, then the previous environment is restored. Entries
    whose value is None are ignored. All validation stays in EnvConfig.
    """

    def __init__(
        self,
        overrides: Mapping[str, str | None],
        settings_file_path: Path = SETTINGS_FILE_PATH,
    ) -> None:
        """Build the configuration with the overrides applied, then restore the environment."""
        applied_overrides = {name: value for name, value in overrides.items() if value is not None}
        previous_values = {name: environ.get(name) for name in applied_overrides}
        environ.update(applied_overrides)
        try:
            super().__init__(settings_file_path)
        finally:
            self._restore_environment(previous_values)

    @staticmethod
    def _restore_environment(previous_values: Mapping[str, str | None]) -> None:
        for name, previous_value in previous_values.items():
            if previous_value is None:
                environ.pop(name, None)
            else:
                environ[name] = previous_value
