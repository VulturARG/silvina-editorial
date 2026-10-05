from os import environ
from unittest import TestCase
from unittest.mock import patch

from src.application.warm_up_language_model_use_case import WarmUpLanguageModelUseCase
from src.domain.language_model.language_model_warmer import LanguageModelWarmer
from src.infrastructure.adapters.llm_generator.noop_language_model_warmup_adapter import (
    NoOpLanguageModelWarmupAdapter,
)
from src.infrastructure.adapters.llm_generator.ollama_backend_error_mapper import (
    OllamaBackendErrorMapper,
)
from src.infrastructure.adapters.llm_generator.ollama_language_model_warmup_adapter import (
    OllamaLanguageModelWarmupAdapter,
)
from src.infrastructure.wirings.warm_up_language_model_use_case_wiring import (
    WarmUpLanguageModelUseCaseWiring,
)


class TestWarmUpLanguageModelUseCaseWiring(TestCase):
    REQUIRED_ENVIRONMENT = {
        "METRICS_DATABASE_PATH": "/custom/path/metrics.db",
        "LOG_FILE_PATH": "/custom/path/silvina.log",
    }

    def test_default_environment_wires_ollama_warmup_adapter(self):
        with patch.dict(environ, self.REQUIRED_ENVIRONMENT, clear=True):
            use_case = WarmUpLanguageModelUseCaseWiring().get_warm_up_language_model_use_case()

        self.assertIsInstance(use_case, WarmUpLanguageModelUseCase)
        self.assertIsInstance(use_case._language_model_warmer, LanguageModelWarmer)
        adapter = use_case._language_model_warmer._language_model_warmup_port
        self.assertIsInstance(adapter, OllamaLanguageModelWarmupAdapter)
        assert isinstance(adapter, OllamaLanguageModelWarmupAdapter)
        self.assertEqual(adapter._model_name, "hf.co/unsloth/gemma-4-26B-A4B-it-GGUF:UD-IQ4_XS")
        self.assertEqual(adapter._base_url, "http://localhost:11434")
        self.assertEqual(adapter._keep_alive, "15m")
        self.assertIsInstance(adapter._error_mapper, OllamaBackendErrorMapper)

    def test_warmup_disabled_via_environment_wires_noop_adapter(self):
        environment = {
            **self.REQUIRED_ENVIRONMENT,
            "OLLAMA_WARMUP_ON_STARTUP": "false",
        }
        with patch.dict(environ, environment, clear=True):
            use_case = WarmUpLanguageModelUseCaseWiring().get_warm_up_language_model_use_case()

        adapter = use_case._language_model_warmer._language_model_warmup_port
        self.assertIsInstance(adapter, NoOpLanguageModelWarmupAdapter)

    def test_debug_mode_with_external_claude_provider_wires_noop_adapter(self):
        environment = {
            **self.REQUIRED_ENVIRONMENT,
            "APP_MODE": "DEBUG",
            "USE_EXTERNAL_LLM": "true",
            "LLM_PROVIDER": "claude",
            "EXTERNAL_LLM_MODEL_NAME": "claude-3-7-sonnet",
        }
        with patch.dict(environ, environment, clear=True):
            use_case = WarmUpLanguageModelUseCaseWiring().get_warm_up_language_model_use_case()

        adapter = use_case._language_model_warmer._language_model_warmup_port
        self.assertIsInstance(adapter, NoOpLanguageModelWarmupAdapter)

    def test_production_mode_with_use_external_llm_true_preserves_ollama_adapter(self):
        environment = {
            **self.REQUIRED_ENVIRONMENT,
            "APP_MODE": "PROD",
            "USE_EXTERNAL_LLM": "true",
            "LLM_PROVIDER": "claude",
        }
        with patch.dict(environ, environment, clear=True):
            use_case = WarmUpLanguageModelUseCaseWiring().get_warm_up_language_model_use_case()

        adapter = use_case._language_model_warmer._language_model_warmup_port
        self.assertIsInstance(adapter, OllamaLanguageModelWarmupAdapter)
        assert isinstance(adapter, OllamaLanguageModelWarmupAdapter)
        self.assertEqual(adapter._model_name, "hf.co/unsloth/gemma-4-26B-A4B-it-GGUF:UD-IQ4_XS")
