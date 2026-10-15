from os import environ
from unittest import TestCase
from unittest.mock import patch

from src.application.ensure_language_model_server_use_case import (
    EnsureLanguageModelServerUseCase,
)
from src.infrastructure.adapters.llm_generator.noop_language_model_server_adapter import (
    NoOpLanguageModelServerAdapter,
)
from src.infrastructure.adapters.llm_generator.ollama_server_adapter import (
    OllamaServerAdapter,
)
from src.infrastructure.overridable_env_config import OverridableEnvConfig
from src.infrastructure.tests.test_doubles.complete_test_environment import (
    CompleteTestEnvironment,
)
from src.infrastructure.wirings.ensure_language_model_server_use_case_wiring import (
    EnsureLanguageModelServerUseCaseWiring,
)


class TestEnsureLanguageModelServerUseCaseWiring(TestCase):
    @staticmethod
    def _complete_environment(overrides: dict[str, str] | None = None) -> dict[str, str]:
        environment = {
            **CompleteTestEnvironment.application_variables(),
            "METRICS_DATABASE_PATH": "/custom/path/metrics.db",
            "LOG_FILE_PATH": "/custom/path/silvina.log",
        }
        if overrides:
            environment.update(overrides)
        return environment

    def test_returns_ensure_language_model_server_use_case(self):
        with patch.dict(environ, self._complete_environment(), clear=True):
            wiring = EnsureLanguageModelServerUseCaseWiring({})
            use_case = wiring.get_ensure_language_model_server_use_case()

        self.assertIsInstance(use_case, EnsureLanguageModelServerUseCase)

    def test_env_config_is_overridable_env_config_built_once_with_overrides(self):
        with patch.dict(environ, self._complete_environment(), clear=True):
            wiring = EnsureLanguageModelServerUseCaseWiring(
                {"OLLAMA_BASE_URL": "http://127.0.0.1:11435"}
            )
            first_config = wiring._env_config()
            second_config = wiring._env_config()

        self.assertIsInstance(first_config, OverridableEnvConfig)
        self.assertIs(first_config, second_config)
        self.assertEqual(first_config.ollama_base_url, "http://127.0.0.1:11435")

    def test_server_adapter_is_ollama_server_adapter_when_ollama_provider(self):
        with patch.dict(environ, self._complete_environment(), clear=True):
            wiring = EnsureLanguageModelServerUseCaseWiring(
                {"OLLAMA_BASE_URL": "http://127.0.0.1:11435"}
            )
            use_case = wiring.get_ensure_language_model_server_use_case()

        server_port = use_case._language_model_server_starter._language_model_server_port
        self.assertIsInstance(server_port, OllamaServerAdapter)
        assert isinstance(server_port, OllamaServerAdapter)
        self.assertEqual(server_port._base_url, "http://127.0.0.1:11435")
        self.assertEqual(server_port._startup_timeout_seconds, 60.0)
        self.assertEqual(server_port._poll_interval_seconds, 0.5)
        self.assertEqual(server_port._probe_timeout_seconds, 2.0)

    def test_server_adapter_is_ollama_server_adapter_even_when_warmup_on_startup_is_false(
        self,
    ):
        with patch.dict(environ, self._complete_environment(), clear=True):
            wiring = EnsureLanguageModelServerUseCaseWiring({"OLLAMA_WARMUP_ON_STARTUP": "false"})
            use_case = wiring.get_ensure_language_model_server_use_case()

        server_port = use_case._language_model_server_starter._language_model_server_port
        self.assertIsInstance(server_port, OllamaServerAdapter)

    def test_server_adapter_is_noop_when_external_provider_is_configured(self):
        overrides = {
            "APP_MODE": "DEBUG",
            "USE_EXTERNAL_LLM": "true",
            "LLM_PROVIDER": "claude",
            "EXTERNAL_LLM_MODEL_NAME": "claude-3-7-sonnet",
        }
        with patch.dict(environ, self._complete_environment(), clear=True):
            wiring = EnsureLanguageModelServerUseCaseWiring(overrides)
            use_case = wiring.get_ensure_language_model_server_use_case()

        server_port = use_case._language_model_server_starter._language_model_server_port
        self.assertIsInstance(server_port, NoOpLanguageModelServerAdapter)

    def test_server_adapter_receives_idle_shutdown_seconds_from_env_config(self):
        overrides = {"OLLAMA_SERVER_IDLE_SHUTDOWN": "10m"}
        with patch.dict(environ, self._complete_environment(), clear=True):
            wiring = EnsureLanguageModelServerUseCaseWiring(overrides)
            use_case = wiring.get_ensure_language_model_server_use_case()

        server_port = use_case._language_model_server_starter._language_model_server_port
        self.assertIsInstance(server_port, OllamaServerAdapter)
        assert isinstance(server_port, OllamaServerAdapter)
        self.assertEqual(server_port._idle_seconds, 600.0)
        assert server_port._watcher_launch_command is not None
        self.assertIn("--idle-seconds", server_port._watcher_launch_command)
        idle_index = server_port._watcher_launch_command.index("--idle-seconds")
        self.assertEqual(server_port._watcher_launch_command[idle_index + 1], "600.0")
