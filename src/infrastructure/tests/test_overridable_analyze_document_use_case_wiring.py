from os import environ
from unittest import TestCase
from unittest.mock import patch

from src.application.analyze_document_use_case import AnalyzeDocumentUseCase
from src.domain.enums.ai_provider import AiProvider
from src.infrastructure.adapters.llm_generator.audited_llm_generator_adapter import (
    AuditedLlmGeneratorAdapter,
)
from src.infrastructure.adapters.llm_generator.ollama_generator_adapter import (
    OllamaGeneratorAdapter,
)
from src.infrastructure.overridable_env_config import OverridableEnvConfig
from src.infrastructure.tests.test_doubles.complete_test_environment import (
    CompleteTestEnvironment,
)
from src.infrastructure.wirings.analyze_document_use_case_wiring import (
    AnalyzeDocumentUseCaseWiring,
)
from src.infrastructure.wirings.external_llm_generator_loader import (
    ExternalLlmGeneratorLoader,
)
from src.infrastructure.wirings.overridable_analyze_document_use_case_wiring import (
    OverridableAnalyzeDocumentUseCaseWiring,
)


class TestOverridableAnalyzeDocumentUseCaseWiring(TestCase):
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

    def test_is_an_analyze_document_use_case_wiring(self):
        self.assertTrue(
            issubclass(OverridableAnalyzeDocumentUseCaseWiring, AnalyzeDocumentUseCaseWiring)
        )

    def test_env_config_is_overridable_env_config_built_once_with_overrides(self):
        with patch.dict(environ, self._complete_environment(), clear=True):
            wiring = OverridableAnalyzeDocumentUseCaseWiring(
                {"OLLAMA_MODEL_NAME": "override-model"}
            )
            first_config = wiring._get_env_config()
            second_config = wiring._get_env_config()

        self.assertIsInstance(first_config, OverridableEnvConfig)
        self.assertIs(first_config, second_config)
        self.assertEqual(first_config.ollama_model_name, "override-model")

    def test_generic_override_key_reaches_env_config(self):
        with patch.dict(environ, self._complete_environment(), clear=True):
            env_config = OverridableAnalyzeDocumentUseCaseWiring(
                {"OLLAMA_NUM_CTX": "16384"}
            )._get_env_config()

        self.assertEqual(env_config.ollama_num_ctx, 16384)

    def test_get_active_model_name_returns_overridden_ollama_model(self):
        with patch.dict(environ, self._complete_environment(), clear=True):
            wiring = OverridableAnalyzeDocumentUseCaseWiring(
                {"OLLAMA_MODEL_NAME": "override-model"}
            )
            active_model_name = wiring.get_active_model_name()

        self.assertEqual(active_model_name, "override-model")

    def test_get_active_model_name_delegates_to_parent_selection(self):
        with patch.object(
            AnalyzeDocumentUseCaseWiring,
            "_get_active_model_name",
            return_value="delegated-model",
        ) as mock_active_model_name:
            active_model_name = OverridableAnalyzeDocumentUseCaseWiring({}).get_active_model_name()

        self.assertEqual(active_model_name, "delegated-model")
        mock_active_model_name.assert_called_once_with()

    def test_create_use_case_builds_ollama_generators_with_overridden_model(self):
        with patch.dict(environ, self._complete_environment(), clear=True):
            use_case = OverridableAnalyzeDocumentUseCaseWiring(
                {"OLLAMA_MODEL_NAME": "override-model"}
            ).create_use_case()

        generators = (
            use_case._article_classifier._llm_generator,
            use_case._quality_analyzer._llm_generator,
            use_case._quality_analyzer._editorial_suitability_analyzer._llm_generator,
        )
        for generator in generators:
            self.assertIsInstance(generator, AuditedLlmGeneratorAdapter)
            assert isinstance(generator, AuditedLlmGeneratorAdapter)
            self.assertEqual(generator._model_name, "override-model")
            self.assertIsInstance(generator._generator, OllamaGeneratorAdapter)
            assert isinstance(generator._generator, OllamaGeneratorAdapter)
            self.assertEqual(generator._generator._model_name, "override-model")

    def test_without_overrides_active_model_name_matches_parent_and_environment(self):
        with patch.dict(environ, self._complete_environment(), clear=True):
            wiring = OverridableAnalyzeDocumentUseCaseWiring({})
            active_model_name = wiring.get_active_model_name()
            parent_active_model_name = AnalyzeDocumentUseCaseWiring()._get_active_model_name()
            use_case = wiring.create_use_case()

        self.assertEqual(active_model_name, self.ENVIRONMENT_MODEL_NAME)
        self.assertEqual(active_model_name, parent_active_model_name)
        self.assertIsInstance(use_case, AnalyzeDocumentUseCase)

    def test_production_mode_ignores_external_llm_overrides_silently(self):
        overrides = {
            "APP_MODE": "PROD",
            "USE_EXTERNAL_LLM": "true",
            "LLM_PROVIDER": "claude",
            "EXTERNAL_LLM_MODEL_NAME": "claude-3-7-sonnet",
        }
        with patch.dict(environ, self._complete_environment(), clear=True):
            wiring = OverridableAnalyzeDocumentUseCaseWiring(overrides)
            active_model_name = wiring.get_active_model_name()
            with patch.object(ExternalLlmGeneratorLoader, "load") as mock_load:
                use_case = wiring.create_use_case()

        self.assertEqual(active_model_name, self.ENVIRONMENT_MODEL_NAME)
        mock_load.assert_not_called()
        classifier_generator = use_case._article_classifier._llm_generator
        self.assertIsInstance(classifier_generator, AuditedLlmGeneratorAdapter)
        assert isinstance(classifier_generator, AuditedLlmGeneratorAdapter)
        self.assertEqual(classifier_generator._provider, AiProvider.OLLAMA)
        self.assertIsInstance(classifier_generator._generator, OllamaGeneratorAdapter)

    def test_debug_mode_external_overrides_select_external_model_name(self):
        overrides = {
            "APP_MODE": "DEBUG",
            "USE_EXTERNAL_LLM": "true",
            "LLM_PROVIDER": "claude",
            "EXTERNAL_LLM_MODEL_NAME": "claude-3-7-sonnet",
        }
        with patch.dict(environ, self._complete_environment(), clear=True):
            wiring = OverridableAnalyzeDocumentUseCaseWiring(overrides)
            active_model_name = wiring.get_active_model_name()
            env_config = wiring._get_env_config()

        self.assertEqual(active_model_name, "claude-3-7-sonnet")
        self.assertEqual(env_config.llm_provider, AiProvider.CLAUDE)

    def test_environment_is_not_modified_after_create_use_case_and_active_model_name(self):
        overrides = {"OLLAMA_MODEL_NAME": "override-model", "LLM_PROVIDER": "claude"}
        with patch.dict(environ, self._complete_environment(), clear=True):
            environment_before = dict(environ)
            wiring = OverridableAnalyzeDocumentUseCaseWiring(overrides)
            wiring.get_active_model_name()
            wiring.create_use_case()
            environment_after = dict(environ)

        self.assertEqual(environment_after, environment_before)
        self.assertNotIn("LLM_PROVIDER", environment_after)

    def test_overrides_do_not_leak_into_plain_parent_wiring(self):
        with patch.dict(environ, self._complete_environment(), clear=True):
            OverridableAnalyzeDocumentUseCaseWiring(
                {"OLLAMA_MODEL_NAME": "override-model"}
            ).get_active_model_name()
            plain_active_model_name = AnalyzeDocumentUseCaseWiring()._get_active_model_name()

        self.assertEqual(plain_active_model_name, self.ENVIRONMENT_MODEL_NAME)
