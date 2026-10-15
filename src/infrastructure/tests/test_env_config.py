from os import environ
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from src.domain.enums.ai_provider import AiProvider
from src.domain.enums.app_mode import AppMode
from src.domain.exceptions.settings_errors import SettingValueMissing
from src.infrastructure.env_config import EnvConfig
from src.infrastructure.tests.test_doubles.complete_test_environment import (
    CompleteTestEnvironment,
)


class TestEnvConfig(TestCase):
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

    def test_missing_required_environment_variable_raises_setting_value_missing(self):
        variables_losing_default = [
            "APP_MODE",
            "LOG_LEVEL",
            "LOG_RETENTION_DAYS",
            "OLLAMA_MODEL_NAME",
            "OLLAMA_BASE_URL",
            "OLLAMA_THINK",
            "OLLAMA_MODEL_KEEP_ALIVE",
            "OLLAMA_WARMUP_ON_STARTUP",
            "USE_EXTERNAL_LLM",
            "EXTERNAL_LLM_THINK",
        ]
        for variable_name in variables_losing_default:
            with self.subTest(variable_name=variable_name):
                environment = self._complete_environment()
                del environment[variable_name]
                with patch.dict(environ, environment, clear=True):
                    with self.assertRaises(SettingValueMissing) as context:
                        EnvConfig()
                    self.assertIn(variable_name, context.exception.dict()["error"])

    def test_blank_required_environment_variable_raises_setting_value_missing(self):
        variables_losing_default = [
            "APP_MODE",
            "LOG_LEVEL",
            "LOG_RETENTION_DAYS",
            "OLLAMA_MODEL_NAME",
            "OLLAMA_BASE_URL",
            "OLLAMA_THINK",
            "OLLAMA_MODEL_KEEP_ALIVE",
            "OLLAMA_WARMUP_ON_STARTUP",
            "USE_EXTERNAL_LLM",
            "EXTERNAL_LLM_THINK",
        ]
        for variable_name in variables_losing_default:
            for blank_value in ["", "   "]:
                with self.subTest(variable_name=variable_name, blank_value=blank_value):
                    environment = self._complete_environment({variable_name: blank_value})
                    with patch.dict(environ, environment, clear=True):
                        with self.assertRaises(SettingValueMissing) as context:
                            EnvConfig()
                        self.assertIn(variable_name, context.exception.dict()["error"])

    def test_reads_version_from_the_version_file_outside_testing_mode(self):
        with TemporaryDirectory() as directory:
            version_file = Path(directory) / "version.txt"
            version_file.write_text("1.2.3\n", encoding="utf-8")
            with patch.dict(environ, self._complete_environment(), clear=True):
                with patch("src.infrastructure.env_config.VERSION_FILE_PATH", version_file):
                    config = EnvConfig()

        self.assertEqual(config.silvina_version, "1.2.3")

    def test_raises_file_not_found_when_version_file_missing_outside_testing(self):
        with patch.dict(environ, self._complete_environment(), clear=True):
            with patch("pathlib.Path.read_text", side_effect=FileNotFoundError):
                with self.assertRaises(FileNotFoundError):
                    EnvConfig()

    def test_testing_mode_falls_back_to_silvina_version_env_var(self):
        with patch.dict(environ, {"TESTING": "True", "SILVINA_VERSION": "0.99"}):
            with patch("pathlib.Path.read_text", side_effect=FileNotFoundError):
                config = EnvConfig()
        self.assertEqual(config.silvina_version, "0.99")

    def test_testing_mode_uses_default_version_when_silvina_version_unset(self):
        environment = self._complete_environment({"TESTING": "True"})
        with patch.dict(environ, environment, clear=True):
            with patch("pathlib.Path.read_text", side_effect=FileNotFoundError):
                config = EnvConfig()
        self.assertEqual(config.silvina_version, "0.9")

    def test_env_var_overrides_citation_max_author_name_length(self):
        with patch.dict(environ, {"CITATION_MAX_AUTHOR_NAME_LENGTH": "150"}):
            config = EnvConfig()
        self.assertEqual(config.citation_max_author_name_length, 150)

    def test_env_var_overrides_grammar_max_replacements(self):
        with patch.dict(environ, {"GRAMMAR_MAX_REPLACEMENTS": "7"}):
            config = EnvConfig()
        self.assertEqual(config.grammar_max_replacements, 7)

    def test_env_var_overrides_structure_max_header_length(self):
        with patch.dict(environ, {"STRUCTURE_MAX_HEADER_LENGTH": "42"}):
            config = EnvConfig()
        self.assertEqual(config.structure_max_header_length, 42)

    def test_env_var_overrides_article_classifier_temperature(self):
        with patch.dict(environ, {"ARTICLE_CLASSIFIER_TEMPERATURE": "0.5"}):
            config = EnvConfig()
        self.assertAlmostEqual(config.article_classifier_temperature, 0.5)

    def test_env_var_overrides_ollama_model_name(self):
        with patch.dict(environ, {"OLLAMA_MODEL_NAME": "custom-model"}):
            config = EnvConfig()
        self.assertEqual(config.ollama_model_name, "custom-model")

    def test_env_var_overrides_ollama_base_url(self):
        with patch.dict(environ, {"OLLAMA_BASE_URL": "http://example.com:1234"}):
            config = EnvConfig()
        self.assertEqual(config.ollama_base_url, "http://example.com:1234")

    def test_env_var_overrides_ollama_think_to_true(self):
        with patch.dict(environ, {"OLLAMA_THINK": "true"}):
            config = EnvConfig()
        self.assertTrue(config.ollama_think)

    def test_env_var_accepts_case_and_whitespace_variations_for_ollama_think(self):
        with patch.dict(environ, {"OLLAMA_THINK": " TRUE "}):
            config_true = EnvConfig()
        self.assertTrue(config_true.ollama_think)

        with patch.dict(environ, {"OLLAMA_THINK": "False"}):
            config_false = EnvConfig()
        self.assertFalse(config_false.ollama_think)

        with patch.dict(environ, {"OLLAMA_THINK": "  false  "}):
            config_spaced_false = EnvConfig()
        self.assertFalse(config_spaced_false.ollama_think)

    def test_invalid_ollama_think_value_raises_value_error(self):
        invalid_values = ["yes", "1"]
        for invalid_value in invalid_values:
            with self.subTest(invalid_value=invalid_value):
                with patch.dict(environ, {"OLLAMA_THINK": invalid_value}):
                    with self.assertRaises(ValueError) as context:
                        EnvConfig()
                    self.assertIn("OLLAMA_THINK", str(context.exception))

    def test_env_var_overrides_ollama_model_keep_alive_with_accepted_values(self):
        accepted_values = ["30m", "1h30m", "90s", "-1m", "500ms"]
        for accepted_value in accepted_values:
            with self.subTest(accepted_value=accepted_value):
                with patch.dict(environ, {"OLLAMA_MODEL_KEEP_ALIVE": accepted_value}):
                    config = EnvConfig()
                self.assertEqual(config.ollama_model_keep_alive, accepted_value)

    def test_env_var_strips_whitespace_for_ollama_model_keep_alive(self):
        with patch.dict(environ, {"OLLAMA_MODEL_KEEP_ALIVE": "  30m  "}):
            config = EnvConfig()
        self.assertEqual(config.ollama_model_keep_alive, "30m")

    def test_invalid_ollama_model_keep_alive_raises_value_error(self):
        rejected_values = ["15", "-1", "15min", "abc"]
        for rejected_value in rejected_values:
            with self.subTest(rejected_value=rejected_value):
                with patch.dict(environ, {"OLLAMA_MODEL_KEEP_ALIVE": rejected_value}):
                    with self.assertRaises(ValueError) as context:
                        EnvConfig()
                    self.assertIn("OLLAMA_MODEL_KEEP_ALIVE", str(context.exception))

    def test_env_var_parses_ollama_server_idle_shutdown_seconds_with_accepted_durations(self):
        cases = [
            ("5m", 300.0),
            ("90s", 90.0),
            ("1h", 3600.0),
            ("1h30m", 5400.0),
            ("500ms", 0.5),
        ]
        for raw_value, expected_seconds in cases:
            with self.subTest(raw_value=raw_value):
                with patch.dict(environ, {"OLLAMA_SERVER_IDLE_SHUTDOWN": raw_value}):
                    config = EnvConfig()
                self.assertEqual(config.ollama_server_idle_shutdown_seconds, expected_seconds)

    def test_env_var_missing_ollama_server_idle_shutdown_raises_setting_value_missing(self):
        environment = self._complete_environment()
        environment.pop("OLLAMA_SERVER_IDLE_SHUTDOWN", None)
        with patch.dict(environ, environment, clear=True):
            with self.assertRaises(SettingValueMissing) as context:
                EnvConfig()
            self.assertIn(
                "OLLAMA_SERVER_IDLE_SHUTDOWN",
                context.exception.dict()["error"],
            )

    def test_env_var_blank_ollama_server_idle_shutdown_raises_setting_value_missing(self):
        for blank_value in ["", "   ", "\t"]:
            with self.subTest(blank_value=blank_value):
                with patch.dict(environ, {"OLLAMA_SERVER_IDLE_SHUTDOWN": blank_value}):
                    with self.assertRaises(SettingValueMissing) as context:
                        EnvConfig()
                    self.assertIn(
                        "OLLAMA_SERVER_IDLE_SHUTDOWN",
                        context.exception.dict()["error"],
                    )

    def test_invalid_ollama_server_idle_shutdown_raises_value_error(self):
        rejected_values = ["0m", "-5m", "5", "abc"]
        for rejected_value in rejected_values:
            with self.subTest(rejected_value=rejected_value):
                with patch.dict(environ, {"OLLAMA_SERVER_IDLE_SHUTDOWN": rejected_value}):
                    with self.assertRaises(ValueError) as context:
                        EnvConfig()
                    self.assertIn("OLLAMA_SERVER_IDLE_SHUTDOWN", str(context.exception))

    def test_default_ollama_num_ctx_when_env_var_absent(self):
        environment = self._complete_environment()
        environment.pop("OLLAMA_NUM_CTX", None)
        with patch.dict(environ, environment, clear=True):
            config = EnvConfig()
        self.assertIsNone(config.ollama_num_ctx)

    def test_ollama_num_ctx_when_env_var_blank_returns_none(self):
        for blank_value in ["", "   ", "\t"]:
            with self.subTest(blank_value=blank_value):
                with patch.dict(environ, {"OLLAMA_NUM_CTX": blank_value}):
                    config = EnvConfig()
                self.assertIsNone(config.ollama_num_ctx)

    def test_env_var_overrides_ollama_num_ctx_with_positive_integer(self):
        with patch.dict(environ, {"OLLAMA_NUM_CTX": "16384"}):
            config = EnvConfig()
        self.assertEqual(config.ollama_num_ctx, 16384)

        with patch.dict(environ, {"OLLAMA_NUM_CTX": "  8192  "}):
            config_spaced = EnvConfig()
        self.assertEqual(config_spaced.ollama_num_ctx, 8192)

        with patch.dict(environ, {"OLLAMA_NUM_CTX": "1"}):
            config_one = EnvConfig()
        self.assertEqual(config_one.ollama_num_ctx, 1)

    def test_invalid_ollama_num_ctx_raises_value_error(self):
        rejected_values = ["0", "-1", "-16384", "abc", "16.5", "16384tokens"]
        for rejected_value in rejected_values:
            with self.subTest(rejected_value=rejected_value):
                with patch.dict(environ, {"OLLAMA_NUM_CTX": rejected_value}):
                    with self.assertRaises(ValueError) as context:
                        EnvConfig()
                    self.assertIn("OLLAMA_NUM_CTX", str(context.exception))
                    self.assertIn(rejected_value, str(context.exception))
                    self.assertIn("positive integer", str(context.exception))

    def test_env_var_overrides_ollama_warmup_on_startup(self):
        with patch.dict(environ, {"OLLAMA_WARMUP_ON_STARTUP": "false"}):
            config_false = EnvConfig()
        self.assertFalse(config_false.ollama_warmup_on_startup)

        with patch.dict(environ, {"OLLAMA_WARMUP_ON_STARTUP": "true"}):
            config_true = EnvConfig()
        self.assertTrue(config_true.ollama_warmup_on_startup)

    def test_env_var_accepts_case_and_whitespace_variations_for_ollama_warmup_on_startup(self):
        with patch.dict(environ, {"OLLAMA_WARMUP_ON_STARTUP": " TRUE "}):
            config_true = EnvConfig()
        self.assertTrue(config_true.ollama_warmup_on_startup)

        with patch.dict(environ, {"OLLAMA_WARMUP_ON_STARTUP": "False"}):
            config_false = EnvConfig()
        self.assertFalse(config_false.ollama_warmup_on_startup)

        with patch.dict(environ, {"OLLAMA_WARMUP_ON_STARTUP": "  false  "}):
            config_spaced_false = EnvConfig()
        self.assertFalse(config_spaced_false.ollama_warmup_on_startup)

    def test_invalid_ollama_warmup_on_startup_raises_value_error(self):
        invalid_values = ["yes", "1"]
        for invalid_value in invalid_values:
            with self.subTest(invalid_value=invalid_value):
                with patch.dict(environ, {"OLLAMA_WARMUP_ON_STARTUP": invalid_value}):
                    with self.assertRaises(ValueError) as context:
                        EnvConfig()
                    self.assertIn("OLLAMA_WARMUP_ON_STARTUP", str(context.exception))

    def test_env_var_overrides_external_llm_think_to_true(self):
        with patch.dict(environ, {"EXTERNAL_LLM_THINK": "true"}):
            config = EnvConfig()
        self.assertTrue(config.external_llm_think)

    def test_env_var_accepts_case_and_whitespace_variations_for_external_llm_think(self):
        with patch.dict(environ, {"EXTERNAL_LLM_THINK": " TRUE "}):
            config_true = EnvConfig()
        self.assertTrue(config_true.external_llm_think)

        with patch.dict(environ, {"EXTERNAL_LLM_THINK": "False"}):
            config_false = EnvConfig()
        self.assertFalse(config_false.external_llm_think)

        with patch.dict(environ, {"EXTERNAL_LLM_THINK": "  false  "}):
            config_spaced_false = EnvConfig()
        self.assertFalse(config_spaced_false.external_llm_think)

    def test_invalid_external_llm_think_value_raises_value_error(self):
        invalid_values = ["yes", "1"]
        for invalid_value in invalid_values:
            with self.subTest(invalid_value=invalid_value):
                with patch.dict(environ, {"EXTERNAL_LLM_THINK": invalid_value}):
                    with self.assertRaises(ValueError) as context:
                        EnvConfig()
                    self.assertIn("EXTERNAL_LLM_THINK", str(context.exception))

    def test_external_llm_think_is_parsed_even_when_external_llm_is_inactive(self):
        environment = self._complete_environment(
            {
                "APP_MODE": "PROD",
                "USE_EXTERNAL_LLM": "false",
                "EXTERNAL_LLM_THINK": "true",
            }
        )
        with patch.dict(environ, environment, clear=True):
            config = EnvConfig()
        self.assertTrue(config.external_llm_think)

    def test_env_var_overrides_quality_threshold(self):
        with patch.dict(environ, {"QUALITY_THRESHOLD": "6.5"}):
            config = EnvConfig()
        self.assertAlmostEqual(config.quality_threshold, 6.5)

    def test_silvina_app_name_defaults_when_env_var_is_absent(self):
        environment = {name: value for name, value in environ.items() if name != "SILVINA_APP_NAME"}
        with patch.dict(environ, environment, clear=True):
            config = EnvConfig()
        self.assertEqual(config.silvina_app_name, "Silvina Editorial Assistant")

    def test_env_var_overrides_silvina_app_name(self):
        with patch.dict(environ, {"SILVINA_APP_NAME": "Custom App"}):
            config = EnvConfig()
        self.assertEqual(config.silvina_app_name, "Custom App")

    def test_env_var_overrides_report_score_high_threshold(self):
        with patch.dict(environ, {"REPORT_SCORE_HIGH_THRESHOLD": "9.0"}):
            config = EnvConfig()
        self.assertAlmostEqual(config.report_score_high_threshold, 9.0)

    def test_env_var_overrides_report_words_per_page(self):
        with patch.dict(environ, {"REPORT_WORDS_PER_PAGE": "300"}):
            config = EnvConfig()
        self.assertEqual(config.report_words_per_page, 300)

    def test_env_var_overrides_upload_max_size_bytes(self):
        with patch.dict(environ, {"UPLOAD_MAX_SIZE_BYTES": "52428800"}):
            config = EnvConfig()
        self.assertEqual(config.upload_max_size_bytes, 52428800)

    def test_int_env_vars_are_cast_to_int(self):
        with patch.dict(environ, {"REPORT_MAX_REPLACEMENTS": "9"}):
            config = EnvConfig()
        self.assertIsInstance(config.report_max_replacements, int)
        self.assertEqual(config.report_max_replacements, 9)

    def test_float_env_vars_are_cast_to_float(self):
        with patch.dict(environ, {"DIMENSION_THRESHOLD": "5"}):
            config = EnvConfig()
        self.assertIsInstance(config.dimension_threshold, float)
        self.assertAlmostEqual(config.dimension_threshold, 5.0)

    def test_get_recommendation_settings_reflects_env_overrides(self):
        overrides = {
            "PUBLISH_THRESHOLD": "8.0",
            "CITATION_COUNT_THRESHOLD": "20",
        }
        with patch.dict(environ, overrides):
            settings = EnvConfig().get_recommendation_settings()

        self.assertAlmostEqual(settings.publish_threshold, 8.0)
        self.assertEqual(settings.citation_count_threshold, 20)

    def test_get_language_tool_settings_reflects_env_overrides(self):
        with patch.dict(environ, {"GRAMMAR_MAX_REPLACEMENTS": "5"}):
            settings = EnvConfig().get_language_tool_settings()

        self.assertEqual(settings.max_replacements, 5)

    def test_env_var_overrides_app_mode_to_debug(self):
        with patch.dict(environ, {"APP_MODE": "DEBUG"}):
            config = EnvConfig()
        self.assertEqual(config.app_mode, AppMode.DEBUG)

    def test_env_var_accepts_lowercase_and_padded_app_mode(self):
        with patch.dict(environ, {"APP_MODE": "debug"}):
            config_lowercase = EnvConfig()
        self.assertEqual(config_lowercase.app_mode, AppMode.DEBUG)

        with patch.dict(environ, {"APP_MODE": "  Prod  "}):
            config_padded = EnvConfig()
        self.assertEqual(config_padded.app_mode, AppMode.PROD)

    def test_invalid_app_mode_raises_value_error(self):
        with patch.dict(environ, {"APP_MODE": "STAGING"}):
            with self.assertRaises(ValueError):
                EnvConfig()

    def test_missing_metrics_database_path_raises_setting_value_missing(self):
        environment = self._complete_environment()
        del environment["METRICS_DATABASE_PATH"]
        with patch.dict(environ, environment, clear=True):
            with self.assertRaises(SettingValueMissing) as context:
                EnvConfig()
        self.assertIn("METRICS_DATABASE_PATH", context.exception.dict()["error"])

    def test_missing_log_file_path_raises_setting_value_missing(self):
        environment = self._complete_environment()
        del environment["LOG_FILE_PATH"]
        with patch.dict(environ, environment, clear=True):
            with self.assertRaises(SettingValueMissing) as context:
                EnvConfig()
        self.assertIn("LOG_FILE_PATH", context.exception.dict()["error"])

    def test_empty_metrics_database_path_raises_setting_value_missing(self):
        environment = self._complete_environment({"METRICS_DATABASE_PATH": ""})
        with patch.dict(environ, environment, clear=True):
            with self.assertRaises(SettingValueMissing) as context:
                EnvConfig()
        self.assertIn("METRICS_DATABASE_PATH", context.exception.dict()["error"])

    def test_whitespace_metrics_database_path_raises_setting_value_missing(self):
        environment = self._complete_environment({"METRICS_DATABASE_PATH": "   "})
        with patch.dict(environ, environment, clear=True):
            with self.assertRaises(SettingValueMissing) as context:
                EnvConfig()
        self.assertIn("METRICS_DATABASE_PATH", context.exception.dict()["error"])

    def test_empty_log_file_path_raises_setting_value_missing(self):
        environment = self._complete_environment({"LOG_FILE_PATH": ""})
        with patch.dict(environ, environment, clear=True):
            with self.assertRaises(SettingValueMissing) as context:
                EnvConfig()
        self.assertIn("LOG_FILE_PATH", context.exception.dict()["error"])

    def test_whitespace_log_file_path_raises_setting_value_missing(self):
        environment = self._complete_environment({"LOG_FILE_PATH": "   "})
        with patch.dict(environ, environment, clear=True):
            with self.assertRaises(SettingValueMissing) as context:
                EnvConfig()
        self.assertIn("LOG_FILE_PATH", context.exception.dict()["error"])

    def test_configured_required_paths_are_stripped_and_returned(self):
        environment = self._complete_environment(
            {
                "METRICS_DATABASE_PATH": "  /custom/path/metrics.db  ",
                "LOG_FILE_PATH": "  /custom/path/silvina.log  ",
            }
        )
        with patch.dict(environ, environment, clear=True):
            config = EnvConfig()
        self.assertEqual(config.metrics_database_path, "/custom/path/metrics.db")
        self.assertEqual(config.log_file_path, "/custom/path/silvina.log")

    def test_env_var_overrides_metrics_database_path(self):
        with patch.dict(environ, {"METRICS_DATABASE_PATH": "/custom/path/metrics.db"}):
            config = EnvConfig()
        self.assertEqual(config.metrics_database_path, "/custom/path/metrics.db")

    def test_env_var_overrides_log_file_path(self):
        with patch.dict(environ, {"LOG_FILE_PATH": "/custom/path/silvina.log"}):
            config = EnvConfig()
        self.assertEqual(config.log_file_path, "/custom/path/silvina.log")

    def test_env_var_overrides_log_level(self):
        with patch.dict(environ, {"LOG_LEVEL": "DEBUG"}):
            config = EnvConfig()
        self.assertEqual(config.log_level, "DEBUG")

    def test_env_var_normalizes_log_level_whitespace_and_casing(self):
        with patch.dict(environ, {"LOG_LEVEL": " debug "}):
            config = EnvConfig()
        self.assertEqual(config.log_level, "DEBUG")

    def test_env_var_overrides_log_retention_days(self):
        with patch.dict(environ, {"LOG_RETENTION_DAYS": "30"}):
            config = EnvConfig()
        self.assertEqual(config.log_retention_days, 30)

    def test_non_integer_log_retention_days_raises_value_error(self):
        with patch.dict(environ, {"LOG_RETENTION_DAYS": "not_an_integer"}):
            with self.assertRaises(ValueError):
                EnvConfig()

    def test_llm_provider_defaults_to_ollama_when_use_external_llm_is_false(self):
        with patch.dict(environ, self._complete_environment(), clear=True):
            config = EnvConfig()
        self.assertFalse(config.use_external_llm)
        self.assertEqual(config.llm_provider, AiProvider.OLLAMA)
        self.assertIsNone(config.external_llm_model_name)

    def test_use_external_llm_flag_true_in_debug_mode_with_claude_sets_attributes(self):
        environment = self._complete_environment(
            {
                "APP_MODE": "DEBUG",
                "USE_EXTERNAL_LLM": "true",
                "LLM_PROVIDER": "claude",
                "EXTERNAL_LLM_MODEL_NAME": "claude-3-5-sonnet",
            }
        )
        with patch.dict(environ, environment, clear=True):
            config = EnvConfig()
        self.assertTrue(config.use_external_llm)
        self.assertEqual(config.llm_provider, AiProvider.CLAUDE)
        self.assertEqual(config.external_llm_model_name, "claude-3-5-sonnet")

    def test_debug_mode_with_external_llm_enabled_without_provider_raises_value_error(self):
        environment = self._complete_environment(
            {
                "APP_MODE": "DEBUG",
                "USE_EXTERNAL_LLM": "true",
                "EXTERNAL_LLM_MODEL_NAME": "claude-3-5-sonnet",
            }
        )
        with patch.dict(environ, environment, clear=True):
            with self.assertRaises(ValueError) as context:
                EnvConfig()
        self.assertIn("LLM_PROVIDER", str(context.exception))

    def test_debug_mode_with_external_llm_enabled_and_blank_provider_raises_value_error(self):
        environment = self._complete_environment(
            {
                "APP_MODE": "DEBUG",
                "USE_EXTERNAL_LLM": "true",
                "LLM_PROVIDER": "   ",
                "EXTERNAL_LLM_MODEL_NAME": "claude-3-5-sonnet",
            }
        )
        with patch.dict(environ, environment, clear=True):
            with self.assertRaises(ValueError) as context:
                EnvConfig()
        self.assertIn("LLM_PROVIDER", str(context.exception))

    def test_debug_mode_with_external_llm_enabled_and_ollama_provider_raises_value_error(self):
        environment = self._complete_environment(
            {
                "APP_MODE": "DEBUG",
                "USE_EXTERNAL_LLM": "true",
                "LLM_PROVIDER": "ollama",
                "EXTERNAL_LLM_MODEL_NAME": "claude-3-5-sonnet",
            }
        )
        with patch.dict(environ, environment, clear=True):
            with self.assertRaises(ValueError) as context:
                EnvConfig()
        self.assertIn("LLM_PROVIDER", str(context.exception))
        self.assertIn("claude", str(context.exception).lower())

    def test_debug_mode_with_external_llm_enabled_without_model_raises_value_error(self):
        environment = self._complete_environment(
            {
                "APP_MODE": "DEBUG",
                "USE_EXTERNAL_LLM": "true",
                "LLM_PROVIDER": "claude",
            }
        )
        with patch.dict(environ, environment, clear=True):
            with self.assertRaises(ValueError) as context:
                EnvConfig()
        self.assertIn("EXTERNAL_LLM_MODEL_NAME", str(context.exception))

    def test_debug_mode_with_external_llm_enabled_and_blank_model_raises_value_error(self):
        environment = self._complete_environment(
            {
                "APP_MODE": "DEBUG",
                "USE_EXTERNAL_LLM": "true",
                "LLM_PROVIDER": "claude",
                "EXTERNAL_LLM_MODEL_NAME": "   ",
            }
        )
        with patch.dict(environ, environment, clear=True):
            with self.assertRaises(ValueError) as context:
                EnvConfig()
        self.assertIn("EXTERNAL_LLM_MODEL_NAME", str(context.exception))

    def test_prod_mode_with_external_llm_flag_true_uses_ollama_and_ignores_provider_and_model(self):
        environment = self._complete_environment(
            {
                "APP_MODE": "PROD",
                "USE_EXTERNAL_LLM": "true",
                "LLM_PROVIDER": "invalid_provider",
                "EXTERNAL_LLM_MODEL_NAME": "   ",
            }
        )
        with patch.dict(environ, environment, clear=True):
            config = EnvConfig()
        self.assertTrue(config.use_external_llm)
        self.assertEqual(config.llm_provider, AiProvider.OLLAMA)
        self.assertIsNone(config.external_llm_model_name)

    def test_debug_mode_with_external_llm_flag_false_ignores_invalid_provider_without_raising(self):
        environment = self._complete_environment(
            {
                "APP_MODE": "DEBUG",
                "USE_EXTERNAL_LLM": "false",
                "LLM_PROVIDER": "invalid_provider",
            }
        )
        with patch.dict(environ, environment, clear=True):
            config = EnvConfig()
        self.assertFalse(config.use_external_llm)
        self.assertEqual(config.llm_provider, AiProvider.OLLAMA)
        self.assertIsNone(config.external_llm_model_name)

    def test_debug_mode_with_external_llm_flag_false_and_claude_set_uses_ollama_and_none_model(
        self,
    ):
        environment = self._complete_environment(
            {
                "APP_MODE": "DEBUG",
                "USE_EXTERNAL_LLM": "false",
                "LLM_PROVIDER": "claude",
                "EXTERNAL_LLM_MODEL_NAME": "claude-3-5-sonnet",
            }
        )
        with patch.dict(environ, environment, clear=True):
            config = EnvConfig()
        self.assertFalse(config.use_external_llm)
        self.assertEqual(config.llm_provider, AiProvider.OLLAMA)
        self.assertIsNone(config.external_llm_model_name)

    def test_invalid_use_external_llm_value_raises_value_error(self):
        invalid_values = ["yes", "1", "disabled"]
        for invalid_value in invalid_values:
            with self.subTest(invalid_value=invalid_value):
                environment = self._complete_environment(
                    {
                        "USE_EXTERNAL_LLM": invalid_value,
                    }
                )
                with patch.dict(environ, environment, clear=True):
                    with self.assertRaises(ValueError) as context:
                        EnvConfig()
                    self.assertIn("USE_EXTERNAL_LLM", str(context.exception))

    def test_external_llm_provider_accepts_case_and_whitespace_variations(self):
        environment = self._complete_environment(
            {
                "APP_MODE": "DEBUG",
                "USE_EXTERNAL_LLM": "true",
                "LLM_PROVIDER": "  CLAUDE  ",
                "EXTERNAL_LLM_MODEL_NAME": "claude-3-5-sonnet",
            }
        )
        with patch.dict(environ, environment, clear=True):
            config = EnvConfig()
        self.assertEqual(config.llm_provider, AiProvider.CLAUDE)

    def test_invalid_external_llm_provider_raises_value_error_listing_accepted_providers(self):
        environment = self._complete_environment(
            {
                "APP_MODE": "DEBUG",
                "USE_EXTERNAL_LLM": "true",
                "LLM_PROVIDER": "invalid_provider",
                "EXTERNAL_LLM_MODEL_NAME": "claude-3-5-sonnet",
            }
        )
        with patch.dict(environ, environment, clear=True):
            with self.assertRaises(ValueError) as context:
                EnvConfig()
        self.assertIn("LLM_PROVIDER", str(context.exception))
        self.assertIn("claude", str(context.exception).lower())

    def test_external_llm_model_name_is_stripped_when_provided(self):
        environment = self._complete_environment(
            {
                "APP_MODE": "DEBUG",
                "USE_EXTERNAL_LLM": "true",
                "LLM_PROVIDER": "claude",
                "EXTERNAL_LLM_MODEL_NAME": "  claude-3-5-sonnet  ",
            }
        )
        with patch.dict(environ, environment, clear=True):
            config = EnvConfig()
        self.assertEqual(config.external_llm_model_name, "claude-3-5-sonnet")

    def test_blank_external_llm_model_name_evaluates_to_none_when_external_llm_inactive(self):
        environment = self._complete_environment(
            {
                "USE_EXTERNAL_LLM": "false",
                "EXTERNAL_LLM_MODEL_NAME": "   ",
            }
        )
        with patch.dict(environ, environment, clear=True):
            config = EnvConfig()
        self.assertIsNone(config.external_llm_model_name)
