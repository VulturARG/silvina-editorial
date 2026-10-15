from os import environ
from pathlib import Path
from tempfile import TemporaryDirectory
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
from src.infrastructure.resources.prompts.classification import (
    PROMPTS_DIR as CLASSIFICATION_PROMPTS_DIR,
)
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

    def test_read_prompt_text_returns_override_content_when_path_is_provided(self):
        temporary_directory = TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        prompt_path = Path(temporary_directory.name) / "s4_s5_s6_signal_prompt.txt"
        prompt_path.write_text("custom signal prompt", encoding="utf-8")

        wiring = OverridableAnalyzeDocumentUseCaseWiring(
            {},
            prompt_file_overrides={"s4_s5_s6_signal_prompt": prompt_path},
        )
        text = wiring._read_prompt_text(
            directory="/nonexistent",
            filename="s4_s5_s6_signal_prompt.txt",
        )

        self.assertEqual(text, "custom signal prompt")

    def test_read_prompt_text_delegates_to_parent_when_override_is_none(self):
        wiring = OverridableAnalyzeDocumentUseCaseWiring(
            {},
            prompt_file_overrides={"s4_s5_s6_signal_prompt": None},
        )
        text = wiring._read_prompt_text(
            directory=CLASSIFICATION_PROMPTS_DIR,
            filename="s4_s5_s6_signal_prompt.txt",
        )

        parent_text = AnalyzeDocumentUseCaseWiring()._read_prompt_text(
            directory=CLASSIFICATION_PROMPTS_DIR,
            filename="s4_s5_s6_signal_prompt.txt",
        )
        self.assertEqual(text, parent_text)

    def test_read_prompt_text_supports_all_six_prompt_keys(self):
        temporary_directory = TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        base_directory = Path(temporary_directory.name)

        keys_and_files = (
            ("s4_s5_s6_signal_prompt", "s4_s5_s6_signal_prompt.txt"),
            ("alignment_prompt", "alignment_prompt.txt"),
            ("argumentation_conclusions_prompt", "argumentation_conclusions_prompt.txt"),
            ("clarity_coherence_prompt", "clarity_coherence_prompt.txt"),
            ("contribution_prompt", "contribution_prompt.txt"),
            ("research_lines", "research_lines.txt"),
        )
        overrides: dict[str, Path | None] = {}
        for key, filename in keys_and_files:
            file_path = base_directory / filename
            file_path.write_text(f"custom content for {key}", encoding="utf-8")
            overrides[key] = file_path

        wiring = OverridableAnalyzeDocumentUseCaseWiring(
            {},
            prompt_file_overrides=overrides,
        )

        for key, filename in keys_and_files:
            text = wiring._read_prompt_text(directory="/nonexistent", filename=filename)
            self.assertEqual(text, f"custom content for {key}")

    def test_create_use_case_injects_overridden_prompt_templates(self):
        temporary_directory = TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        base_directory = Path(temporary_directory.name)

        keys_and_files = (
            ("s4_s5_s6_signal_prompt", "s4_s5_s6_signal_prompt.txt"),
            ("alignment_prompt", "alignment_prompt.txt"),
            ("argumentation_conclusions_prompt", "argumentation_conclusions_prompt.txt"),
            ("clarity_coherence_prompt", "clarity_coherence_prompt.txt"),
            ("contribution_prompt", "contribution_prompt.txt"),
            ("research_lines", "research_lines.txt"),
        )
        overrides: dict[str, Path | None] = {}
        for key, filename in keys_and_files:
            file_path = base_directory / filename
            file_path.write_text(f"custom content for {key}", encoding="utf-8")
            overrides[key] = file_path

        with patch.dict(environ, self._complete_environment(), clear=True):
            use_case = OverridableAnalyzeDocumentUseCaseWiring(
                {},
                prompt_file_overrides=overrides,
            ).create_use_case()

        self.assertEqual(
            use_case._article_classifier._signal_prompt_template,
            "custom content for s4_s5_s6_signal_prompt",
        )
        self.assertEqual(
            use_case._quality_analyzer._clarity_coherence_prompt_template,
            "custom content for clarity_coherence_prompt",
        )
        self.assertEqual(
            use_case._quality_analyzer._argumentation_conclusions_prompt_template,
            "custom content for argumentation_conclusions_prompt",
        )
        suitability_analyzer = use_case._quality_analyzer._editorial_suitability_analyzer
        self.assertEqual(
            suitability_analyzer._contribution_prompt_template,
            "custom content for contribution_prompt",
        )
        self.assertEqual(
            suitability_analyzer._alignment_prompt_template,
            "custom content for alignment_prompt",
        )
        self.assertEqual(
            suitability_analyzer._research_lines,
            "custom content for research_lines",
        )

    def test_uses_local_language_model_returns_true_for_ollama(self):
        with patch.dict(environ, self._complete_environment(), clear=True):
            wiring = OverridableAnalyzeDocumentUseCaseWiring({})
            self.assertTrue(wiring.uses_local_language_model())

    def test_uses_local_language_model_returns_false_for_external_provider(self):
        overrides = {
            "APP_MODE": "DEBUG",
            "USE_EXTERNAL_LLM": "true",
            "LLM_PROVIDER": "claude",
            "EXTERNAL_LLM_MODEL_NAME": "claude-3-7-sonnet",
        }
        with patch.dict(environ, self._complete_environment(), clear=True):
            wiring = OverridableAnalyzeDocumentUseCaseWiring(overrides)
            self.assertFalse(wiring.uses_local_language_model())

    def test_warms_up_language_model_returns_true_when_local_and_enabled(self):
        with patch.dict(environ, self._complete_environment(), clear=True):
            wiring = OverridableAnalyzeDocumentUseCaseWiring({"OLLAMA_WARMUP_ON_STARTUP": "true"})
            self.assertTrue(wiring.warms_up_language_model())

    def test_warms_up_language_model_returns_false_when_startup_warmup_disabled(self):
        with patch.dict(environ, self._complete_environment(), clear=True):
            wiring = OverridableAnalyzeDocumentUseCaseWiring({"OLLAMA_WARMUP_ON_STARTUP": "false"})
            self.assertFalse(wiring.warms_up_language_model())

    def test_warms_up_language_model_returns_false_for_external_provider(self):
        overrides = {
            "APP_MODE": "DEBUG",
            "USE_EXTERNAL_LLM": "true",
            "LLM_PROVIDER": "claude",
            "EXTERNAL_LLM_MODEL_NAME": "claude-3-7-sonnet",
            "OLLAMA_WARMUP_ON_STARTUP": "true",
        }
        with patch.dict(environ, self._complete_environment(), clear=True):
            wiring = OverridableAnalyzeDocumentUseCaseWiring(overrides)
            self.assertFalse(wiring.warms_up_language_model())
