from os import environ
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from src.domain.enums.ai_provider import AiProvider
from src.domain.enums.app_mode import AppMode
from src.infrastructure.env_config import EnvConfig
from src.infrastructure.overridable_env_config import OverridableEnvConfig
from src.infrastructure.tests.test_doubles.complete_test_environment import (
    CompleteTestEnvironment,
)
from src.infrastructure.tests.test_doubles.complete_test_settings import (
    CompleteTestSettings,
)


class TestOverridableEnvConfig(TestCase):
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

    def test_ollama_model_name_override_wins_over_environment_value(self):
        with patch.dict(environ, self._complete_environment(), clear=True):
            config = OverridableEnvConfig({"OLLAMA_MODEL_NAME": "gemma-from-cli"})

        self.assertEqual(config.ollama_model_name, "gemma-from-cli")

    def test_without_overrides_values_match_env_config(self):
        with patch.dict(environ, self._complete_environment(), clear=True):
            overridable_config = OverridableEnvConfig({})
            plain_config = EnvConfig()

        self.assertEqual(vars(overridable_config), vars(plain_config))

    def test_none_override_values_are_ignored(self):
        with patch.dict(environ, self._complete_environment(), clear=True):
            config = OverridableEnvConfig(
                {"OLLAMA_MODEL_NAME": None, "USE_EXTERNAL_LLM": None, "LLM_PROVIDER": None}
            )

        self.assertEqual(config.ollama_model_name, "gemma4-26b-adapted")
        self.assertFalse(config.use_external_llm)
        self.assertEqual(config.llm_provider, AiProvider.OLLAMA)

    def test_debug_mode_overrides_enable_external_provider_and_model(self):
        overrides = {
            "APP_MODE": "DEBUG",
            "USE_EXTERNAL_LLM": "true",
            "LLM_PROVIDER": "claude",
            "EXTERNAL_LLM_MODEL_NAME": "claude-3-5-sonnet",
        }
        with patch.dict(environ, self._complete_environment(), clear=True):
            config = OverridableEnvConfig(overrides)

        self.assertEqual(config.app_mode, AppMode.DEBUG)
        self.assertTrue(config.use_external_llm)
        self.assertEqual(config.llm_provider, AiProvider.CLAUDE)
        self.assertEqual(config.external_llm_model_name, "claude-3-5-sonnet")

    def test_prod_mode_silently_ignores_external_llm_overrides(self):
        overrides = {
            "USE_EXTERNAL_LLM": "true",
            "LLM_PROVIDER": "claude",
            "EXTERNAL_LLM_MODEL_NAME": "claude-3-5-sonnet",
        }
        with patch.dict(environ, self._complete_environment(), clear=True):
            config = OverridableEnvConfig(overrides)

        self.assertEqual(config.app_mode, AppMode.PROD)
        self.assertTrue(config.use_external_llm)
        self.assertEqual(config.llm_provider, AiProvider.OLLAMA)
        self.assertIsNone(config.external_llm_model_name)

    def test_use_external_llm_false_override_disables_true_environment_value(self):
        environment = self._complete_environment(
            {
                "APP_MODE": "DEBUG",
                "USE_EXTERNAL_LLM": "true",
                "LLM_PROVIDER": "claude",
                "EXTERNAL_LLM_MODEL_NAME": "claude-3-5-sonnet",
            }
        )
        with patch.dict(environ, environment, clear=True):
            config = OverridableEnvConfig({"USE_EXTERNAL_LLM": "false"})

        self.assertFalse(config.use_external_llm)
        self.assertEqual(config.llm_provider, AiProvider.OLLAMA)
        self.assertIsNone(config.external_llm_model_name)

    def test_changed_environment_variable_gets_its_previous_value_back(self):
        with patch.dict(environ, self._complete_environment(), clear=True):
            OverridableEnvConfig({"OLLAMA_MODEL_NAME": "gemma-from-cli"})

            restored_value = environ["OLLAMA_MODEL_NAME"]

        self.assertEqual(restored_value, "gemma4-26b-adapted")

    def test_variable_absent_before_construction_is_removed_afterwards(self):
        with patch.dict(environ, self._complete_environment(), clear=True):
            OverridableEnvConfig({"LLM_PROVIDER": "claude"})

            is_still_present = "LLM_PROVIDER" in environ

        self.assertFalse(is_still_present)

    def test_environment_is_restored_when_constructor_raises(self):
        overrides = {
            "USE_EXTERNAL_LLM": "maybe",
            "EXTERNAL_LLM_MODEL_NAME": "claude-3-5-sonnet",
        }
        with patch.dict(environ, self._complete_environment(), clear=True):
            with self.assertRaises(ValueError):
                OverridableEnvConfig(overrides)

            restored_use_external_llm = environ["USE_EXTERNAL_LLM"]
            is_model_name_still_present = "EXTERNAL_LLM_MODEL_NAME" in environ

        self.assertEqual(restored_use_external_llm, "false")
        self.assertFalse(is_model_name_still_present)

    def test_invalid_override_raises_the_same_value_error_as_env_config(self):
        with patch.dict(
            environ, self._complete_environment({"USE_EXTERNAL_LLM": "yes"}), clear=True
        ):
            with self.assertRaises(ValueError) as plain_context:
                EnvConfig()
        with patch.dict(environ, self._complete_environment(), clear=True):
            with self.assertRaises(ValueError) as overridable_context:
                OverridableEnvConfig({"USE_EXTERNAL_LLM": "yes"})

        self.assertEqual(str(overridable_context.exception), str(plain_context.exception))

    def test_settings_file_path_is_forwarded_to_env_config(self):
        with TemporaryDirectory() as directory:
            settings_file_path = Path(directory) / "settings.toml"
            settings_file_path.write_text(
                CompleteTestSettings.toml_text({"citation_max_author_name_length": 77}),
                encoding="utf-8",
            )
            with patch.dict(environ, self._complete_environment(), clear=True):
                config = OverridableEnvConfig({}, settings_file_path=settings_file_path)

        self.assertEqual(config.citation_max_author_name_length, 77)

    def test_ollama_server_idle_shutdown_override_wins_over_environment_value(self):
        with patch.dict(environ, self._complete_environment(), clear=True):
            config = OverridableEnvConfig({"OLLAMA_SERVER_IDLE_SHUTDOWN": "10m"})

        self.assertEqual(config.ollama_server_idle_shutdown_seconds, 600.0)
