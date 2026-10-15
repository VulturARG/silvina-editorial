from os import environ
from unittest import TestCase
from unittest.mock import patch

from src.application.release_language_model_server_use_case import (
    ReleaseLanguageModelServerUseCase,
)
from src.infrastructure.adapters.llm_generator.noop_language_model_server_adapter import (
    NoOpLanguageModelServerAdapter,
)
from src.infrastructure.adapters.llm_generator.ollama_server_adapter import (
    OllamaServerAdapter,
)
from src.infrastructure.tests.test_doubles.complete_test_environment import (
    CompleteTestEnvironment,
)
from src.infrastructure.wirings.ensure_language_model_server_use_case_wiring import (
    EnsureLanguageModelServerUseCaseWiring,
)
from src.infrastructure.wirings.release_language_model_server_use_case_wiring import (
    ReleaseLanguageModelServerUseCaseWiring,
)


class TestReleaseLanguageModelServerUseCaseWiring(TestCase):
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

    def test_returns_release_language_model_server_use_case(self):
        with patch.dict(environ, self._complete_environment(), clear=True):
            wiring = ReleaseLanguageModelServerUseCaseWiring({})
            use_case = wiring.get_release_language_model_server_use_case()

        self.assertIsInstance(use_case, ReleaseLanguageModelServerUseCase)

    def test_server_adapter_is_ollama_server_adapter_when_ollama_provider(self):
        with patch.dict(environ, self._complete_environment(), clear=True):
            wiring = ReleaseLanguageModelServerUseCaseWiring(
                {"OLLAMA_BASE_URL": "http://127.0.0.1:11435"}
            )
            use_case = wiring.get_release_language_model_server_use_case()

        server_port = use_case._language_model_server_starter._language_model_server_port
        self.assertIsInstance(server_port, OllamaServerAdapter)
        assert isinstance(server_port, OllamaServerAdapter)
        self.assertEqual(server_port._base_url, "http://127.0.0.1:11435")

    def test_server_adapter_is_noop_when_external_provider_is_configured(self):
        overrides = {
            "APP_MODE": "DEBUG",
            "USE_EXTERNAL_LLM": "true",
            "LLM_PROVIDER": "claude",
            "EXTERNAL_LLM_MODEL_NAME": "claude-3-7-sonnet",
        }
        with patch.dict(environ, self._complete_environment(), clear=True):
            wiring = ReleaseLanguageModelServerUseCaseWiring(overrides)
            use_case = wiring.get_release_language_model_server_use_case()

        server_port = use_case._language_model_server_starter._language_model_server_port
        self.assertIsInstance(server_port, NoOpLanguageModelServerAdapter)

    def test_ensure_and_release_wirings_use_same_lease_file_path(self):
        with patch.dict(environ, self._complete_environment(), clear=True):
            ensure_wiring = EnsureLanguageModelServerUseCaseWiring({})
            release_wiring = ReleaseLanguageModelServerUseCaseWiring({})

        ensure_port = ensure_wiring.get_ensure_language_model_server_use_case()._language_model_server_starter._language_model_server_port
        release_port = release_wiring.get_release_language_model_server_use_case()._language_model_server_starter._language_model_server_port

        assert isinstance(ensure_port, OllamaServerAdapter)
        assert isinstance(release_port, OllamaServerAdapter)
        self.assertIsNotNone(ensure_port._lease_store)
        self.assertIsNotNone(release_port._lease_store)
        assert ensure_port._lease_store is not None
        assert release_port._lease_store is not None
        self.assertEqual(ensure_port._lease_store._path, release_port._lease_store._path)
