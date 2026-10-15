from collections.abc import Mapping
from os import getpid
from pathlib import Path
from sys import executable
from time import time

from src.domain.enums.ai_provider import AiProvider
from src.domain.language_model.language_model_server_port import (
    LanguageModelServerPort,
)
from src.domain.language_model.language_model_server_starter import (
    LanguageModelServerStarter,
)
from src.infrastructure.adapters.llm_generator.noop_language_model_server_adapter import (
    NoOpLanguageModelServerAdapter,
)
from src.infrastructure.adapters.llm_generator.ollama_executable_locator import (
    OllamaExecutableLocator,
)
from src.infrastructure.adapters.llm_generator.ollama_server_adapter import (
    OllamaServerAdapter,
)
from src.infrastructure.adapters.llm_generator.ollama_server_lease_store import (
    OllamaServerLeaseStore,
)
from src.infrastructure.adapters.llm_generator.process_inspector import (
    ProcessInspector,
)
from src.infrastructure.overridable_env_config import OverridableEnvConfig
from src.infrastructure.resources.project import PROJECT_ROOT_DIR


class LanguageModelServerWiring:
    """Base wiring providing configured language model server adapter and starter."""

    STARTUP_TIMEOUT_SECONDS: float = 60.0
    POLL_INTERVAL_SECONDS: float = 0.5
    PROBE_TIMEOUT_SECONDS: float = 2.0
    WATCHER_POLL_INTERVAL_SECONDS: float = 10.0
    LEASE_FILE_PATH: Path = PROJECT_ROOT_DIR / "data" / "ollama_server_lease.json"

    def __init__(self, environment_overrides: Mapping[str, str | None]) -> None:
        """Keep the environment overrides applied to the server configuration."""
        self._environment_overrides = dict(environment_overrides)
        self._env_config_instance: OverridableEnvConfig | None = None

    def _language_model_server_starter(self) -> LanguageModelServerStarter:
        return LanguageModelServerStarter(
            language_model_server_port=self._language_model_server_port()
        )

    def _language_model_server_port(self) -> LanguageModelServerPort:
        env_config = self._env_config()
        if env_config.llm_provider is AiProvider.OLLAMA:
            idle_shutdown_seconds = env_config.ollama_server_idle_shutdown_seconds
            watcher_launch_command = [
                executable,
                "-m",
                "src.infrastructure.cli.ollama_idle_shutdown_watcher_main",
                "--idle-seconds",
                str(idle_shutdown_seconds),
                "--poll-interval-seconds",
                str(self.WATCHER_POLL_INTERVAL_SECONDS),
                "--lease-file",
                str(self.LEASE_FILE_PATH),
            ]
            return OllamaServerAdapter(
                base_url=env_config.ollama_base_url,
                startup_timeout_seconds=self.STARTUP_TIMEOUT_SECONDS,
                poll_interval_seconds=self.POLL_INTERVAL_SECONDS,
                probe_timeout_seconds=self.PROBE_TIMEOUT_SECONDS,
                executable_locator=self._ollama_executable_locator().locate,
                lease_store=OllamaServerLeaseStore(self.LEASE_FILE_PATH),
                process_inspector=ProcessInspector(),
                current_process_id_provider=getpid,
                wall_clock_function=time,
                watcher_launch_command=watcher_launch_command,
                watcher_working_directory=PROJECT_ROOT_DIR,
                idle_seconds=idle_shutdown_seconds,
            )
        return NoOpLanguageModelServerAdapter()

    def _ollama_executable_locator(self) -> OllamaExecutableLocator:
        return OllamaExecutableLocator()

    def _env_config(self) -> OverridableEnvConfig:
        if self._env_config_instance is None:
            self._env_config_instance = OverridableEnvConfig(self._environment_overrides)
        return self._env_config_instance
