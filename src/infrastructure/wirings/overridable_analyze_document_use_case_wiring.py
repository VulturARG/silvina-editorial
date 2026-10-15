from collections.abc import Mapping
from pathlib import Path

from src.domain.enums.ai_provider import AiProvider
from src.infrastructure.env_config import EnvConfig
from src.infrastructure.overridable_env_config import OverridableEnvConfig
from src.infrastructure.resources.text_resource_loader import read_text_resource
from src.infrastructure.wirings.analyze_document_use_case_wiring import (
    AnalyzeDocumentUseCaseWiring,
)


class OverridableAnalyzeDocumentUseCaseWiring(AnalyzeDocumentUseCaseWiring):
    """Analysis composition root whose whole pipeline uses environment overrides."""

    def __init__(
        self,
        environment_overrides: Mapping[str, str | None],
        prompt_file_overrides: Mapping[str, Path | None] | None = None,
    ) -> None:
        """Keep the overrides applied to the configuration and prompts built for the pipeline."""
        super().__init__()
        self._environment_overrides = dict(environment_overrides)
        self._prompt_file_overrides = (
            dict(prompt_file_overrides) if prompt_file_overrides is not None else {}
        )

    def get_active_model_name(self) -> str:
        """Return the effective model name with the overrides applied."""
        return self._get_active_model_name()

    def uses_local_language_model(self) -> bool:
        """Return True when the configured language model provider is Ollama."""
        return self._get_env_config().llm_provider is AiProvider.OLLAMA

    def warms_up_language_model(self) -> bool:
        """Return True when using local Ollama and startup warm-up is enabled."""
        env_config = self._get_env_config()
        return self.uses_local_language_model() and env_config.ollama_warmup_on_startup

    def _get_env_config(self) -> EnvConfig:
        if self._env_config_instance is None:
            self._env_config_instance = OverridableEnvConfig(self._environment_overrides)
        return self._env_config_instance

    def _read_prompt_text(self, directory: str, filename: str) -> str:
        prompt_key = Path(filename).stem
        override_path = self._prompt_file_overrides.get(prompt_key)
        if override_path is not None:
            return read_text_resource(
                directory=str(override_path.parent),
                filename=override_path.name,
            )
        return super()._read_prompt_text(directory=directory, filename=filename)
