from os import environ
from unittest import TestCase
from unittest.mock import patch

from src.application.warm_up_language_model_use_case import WarmUpLanguageModelUseCase
from src.infrastructure.adapters.llm_generator.noop_language_model_warmup_adapter import (
    NoOpLanguageModelWarmupAdapter,
)
from src.infrastructure.adapters.llm_generator.ollama_language_model_warmup_adapter import (
    OllamaLanguageModelWarmupAdapter,
)
from src.infrastructure.overridable_env_config import OverridableEnvConfig
from src.infrastructure.tests.test_doubles.complete_test_environment import (
    CompleteTestEnvironment,
)
from src.infrastructure.wirings.overridable_warm_up_language_model_use_case_wiring import (
    OverridableWarmUpLanguageModelUseCaseWiring,
)
from src.infrastructure.wirings.warm_up_language_model_use_case_wiring import (
    WarmUpLanguageModelUseCaseWiring,
)


class TestOverridableWarmUpLanguageModelUseCaseWiring(TestCase):
    ENVIRONMENT_MODEL_NAME = "gemma4-26b-adapted"

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

    def test_is_subclass_of_warm_up_language_model_use_case_wiring(self):
        self.assertTrue(
            issubclass(
                OverridableWarmUpLanguageModelUseCaseWiring,
                WarmUpLanguageModelUseCaseWiring,
            )
        )

    def test_env_config_is_overridable_env_config_built_once_with_overrides(self):
        with patch.dict(environ, self._complete_environment(), clear=True):
            wiring = OverridableWarmUpLanguageModelUseCaseWiring(
                {"OLLAMA_MODEL_NAME": "override-model"}
            )
            first_config = wiring._env_config()
            second_config = wiring._env_config()

        self.assertIsInstance(first_config, OverridableEnvConfig)
        self.assertIs(first_config, second_config)
        self.assertEqual(first_config.ollama_model_name, "override-model")

    def test_warmup_adapter_uses_overridden_model_name_when_ollama_provider_and_warmup_enabled(
        self,
    ):
        with patch.dict(environ, self._complete_environment(), clear=True):
            wiring = OverridableWarmUpLanguageModelUseCaseWiring(
                {"OLLAMA_MODEL_NAME": "override-model"}
            )
            use_case = wiring.get_warm_up_language_model_use_case()

        self.assertIsInstance(use_case, WarmUpLanguageModelUseCase)
        warmer_port = use_case._language_model_warmer._language_model_warmup_port
        self.assertIsInstance(warmer_port, OllamaLanguageModelWarmupAdapter)
        assert isinstance(warmer_port, OllamaLanguageModelWarmupAdapter)
        self.assertEqual(warmer_port._model_name, "override-model")

    def test_warmup_adapter_is_noop_when_external_provider_is_configured_in_debug_mode(
        self,
    ):
        overrides = {
            "APP_MODE": "DEBUG",
            "USE_EXTERNAL_LLM": "true",
            "LLM_PROVIDER": "claude",
            "EXTERNAL_LLM_MODEL_NAME": "claude-3-7-sonnet",
        }
        with patch.dict(environ, self._complete_environment(), clear=True):
            wiring = OverridableWarmUpLanguageModelUseCaseWiring(overrides)
            use_case = wiring.get_warm_up_language_model_use_case()

        warmer_port = use_case._language_model_warmer._language_model_warmup_port
        self.assertIsInstance(warmer_port, NoOpLanguageModelWarmupAdapter)

    def test_warmup_adapter_is_noop_when_warmup_on_startup_is_overridden_to_false(self):
        with patch.dict(environ, self._complete_environment(), clear=True):
            wiring = OverridableWarmUpLanguageModelUseCaseWiring(
                {"OLLAMA_WARMUP_ON_STARTUP": "false"}
            )
            use_case = wiring.get_warm_up_language_model_use_case()

        warmer_port = use_case._language_model_warmer._language_model_warmup_port
        self.assertIsInstance(warmer_port, NoOpLanguageModelWarmupAdapter)

    def test_warmup_adapter_uses_environment_model_when_no_overrides_given(self):
        with patch.dict(environ, self._complete_environment(), clear=True):
            wiring = OverridableWarmUpLanguageModelUseCaseWiring({})
            use_case = wiring.get_warm_up_language_model_use_case()

        warmer_port = use_case._language_model_warmer._language_model_warmup_port
        self.assertIsInstance(warmer_port, OllamaLanguageModelWarmupAdapter)
        assert isinstance(warmer_port, OllamaLanguageModelWarmupAdapter)
        self.assertEqual(warmer_port._model_name, self.ENVIRONMENT_MODEL_NAME)
