from os import environ
from unittest import TestCase
from unittest.mock import patch

from src.domain.dtos.recommendation_settings_dto import RecommendationSettingsDTO
from src.domain.enums.app_mode import AppMode
from src.infrastructure.env_config import EnvConfig


class TestEnvConfig(TestCase):
    REQUIRED_ENVIRONMENT = {
        "METRICS_DATABASE_PATH": "/custom/path/metrics.db",
        "LOG_FILE_PATH": "/custom/path/silvina.log",
    }

    def test_defaults_are_loaded_when_env_is_empty(self):
        with patch.dict(environ, self.REQUIRED_ENVIRONMENT, clear=True):
            config = EnvConfig()

        self.assertEqual(config.citation_max_author_name_length, 100)
        self.assertEqual(config.grammar_max_replacements, 3)
        self.assertEqual(config.structure_max_header_length, 100)
        self.assertAlmostEqual(config.article_classifier_temperature, 0.1)
        self.assertEqual(config.article_classifier_num_predict, 300)
        self.assertEqual(config.article_size_short_min_chars, 16000)
        self.assertEqual(config.article_size_short_max_chars, 24000)
        self.assertEqual(config.article_size_undefined_min_chars, 24001)
        self.assertEqual(config.article_size_undefined_max_chars, 35999)
        self.assertEqual(config.article_size_long_min_chars, 36000)
        self.assertEqual(config.article_size_long_max_chars, 40000)
        self.assertAlmostEqual(config.quality_level_excellent_threshold, 9.0)
        self.assertAlmostEqual(config.quality_level_good_threshold, 7.0)
        self.assertAlmostEqual(config.quality_level_acceptable_threshold, 5.0)
        self.assertAlmostEqual(config.quality_level_needs_improvement_threshold, 3.0)
        self.assertEqual(config.quality_min_sample_word_count, 400)
        self.assertEqual(config.quality_text_sample_character_limit, 8000)
        self.assertEqual(
            config.ollama_model_name, "hf.co/unsloth/gemma-4-26B-A4B-it-GGUF:UD-IQ4_XS"
        )
        self.assertEqual(config.ollama_base_url, "http://localhost:11434")
        self.assertAlmostEqual(config.publish_threshold, 7.0)
        self.assertAlmostEqual(config.quality_threshold, 7.0)
        self.assertAlmostEqual(config.grammar_threshold, 7.0)
        self.assertAlmostEqual(config.dimension_threshold, 6.0)
        self.assertAlmostEqual(config.citation_match_threshold, 90.0)
        self.assertAlmostEqual(config.critical_citation_match_threshold, 50.0)
        self.assertEqual(config.citation_count_threshold, 10)
        self.assertAlmostEqual(config.classification_confidence_threshold, 0.7)
        self.assertAlmostEqual(config.critical_quality_threshold, 5.0)
        self.assertAlmostEqual(config.critical_grammar_threshold, 5.0)
        self.assertEqual(config.silvina_app_name, "Silvina Editorial Assistant")
        self.assertEqual(config.silvina_version, "0.95")
        self.assertAlmostEqual(config.report_score_high_threshold, 8.0)
        self.assertAlmostEqual(config.report_score_medium_threshold, 6.0)
        self.assertEqual(config.report_words_per_page, 250)
        self.assertEqual(config.report_max_errors_displayed, 5)
        self.assertEqual(config.report_context_truncation_limit, 150)
        self.assertEqual(config.report_max_replacements, 3)
        self.assertEqual(config.upload_max_size_bytes, 26214400)
        self.assertEqual(config.app_mode, AppMode.PROD)
        self.assertEqual(config.metrics_database_path, "/custom/path/metrics.db")
        self.assertEqual(config.log_file_path, "/custom/path/silvina.log")
        self.assertEqual(config.log_level, "INFO")
        self.assertEqual(config.log_retention_days, 14)

    def test_raises_file_not_found_when_version_file_missing_outside_testing(self):
        with patch.dict(environ, self.REQUIRED_ENVIRONMENT, clear=True):
            with patch("pathlib.Path.read_text", side_effect=FileNotFoundError):
                with self.assertRaises(FileNotFoundError):
                    EnvConfig()

    def test_testing_mode_falls_back_to_silvina_version_env_var(self):
        with patch.dict(environ, {"TESTING": "True", "SILVINA_VERSION": "0.99"}):
            with patch("pathlib.Path.read_text", side_effect=FileNotFoundError):
                config = EnvConfig()
        self.assertEqual(config.silvina_version, "0.99")

    def test_testing_mode_uses_default_version_when_silvina_version_unset(self):
        environment = {**self.REQUIRED_ENVIRONMENT, "TESTING": "True"}
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

    def test_env_var_overrides_quality_threshold(self):
        with patch.dict(environ, {"QUALITY_THRESHOLD": "6.5"}):
            config = EnvConfig()
        self.assertAlmostEqual(config.quality_threshold, 6.5)

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

    def test_get_recommendation_settings_returns_dto_with_defaults(self):
        with patch.dict(environ, self.REQUIRED_ENVIRONMENT, clear=True):
            config = EnvConfig()
            settings = config.get_recommendation_settings()

        self.assertIsInstance(settings, RecommendationSettingsDTO)
        self.assertAlmostEqual(settings.publish_threshold, 7.0)
        self.assertAlmostEqual(settings.quality_threshold, 7.0)
        self.assertAlmostEqual(settings.grammar_threshold, 7.0)
        self.assertAlmostEqual(settings.dimension_threshold, 6.0)
        self.assertAlmostEqual(settings.citation_match_threshold, 90.0)
        self.assertAlmostEqual(settings.critical_citation_match_threshold, 50.0)
        self.assertEqual(settings.citation_count_threshold, 10)
        self.assertAlmostEqual(settings.classification_confidence_threshold, 0.7)
        self.assertAlmostEqual(settings.critical_quality_threshold, 5.0)
        self.assertAlmostEqual(settings.critical_grammar_threshold, 5.0)

    def test_get_recommendation_settings_reflects_env_overrides(self):
        overrides = {
            "PUBLISH_THRESHOLD": "8.0",
            "CITATION_COUNT_THRESHOLD": "20",
        }
        with patch.dict(environ, overrides):
            settings = EnvConfig().get_recommendation_settings()

        self.assertAlmostEqual(settings.publish_threshold, 8.0)
        self.assertEqual(settings.citation_count_threshold, 20)

    def test_app_mode_defaults_to_prod_when_env_is_empty(self):
        with patch.dict(environ, self.REQUIRED_ENVIRONMENT, clear=True):
            config = EnvConfig()
        self.assertEqual(config.app_mode, AppMode.PROD)

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

    def test_empty_app_mode_raises_value_error(self):
        with patch.dict(environ, {"APP_MODE": ""}):
            with self.assertRaises(ValueError):
                EnvConfig()

    def test_logging_defaults_are_loaded_when_env_is_empty(self):
        with patch.dict(environ, self.REQUIRED_ENVIRONMENT, clear=True):
            config = EnvConfig()
        self.assertEqual(config.log_level, "INFO")
        self.assertEqual(config.log_retention_days, 14)

    def test_missing_metrics_database_path_raises_value_error(self):
        environment = {"LOG_FILE_PATH": "/custom/path/silvina.log"}
        with patch.dict(environ, environment, clear=True):
            with self.assertRaises(ValueError) as context:
                EnvConfig()
        self.assertIn("METRICS_DATABASE_PATH", str(context.exception))

    def test_missing_log_file_path_raises_value_error(self):
        environment = {"METRICS_DATABASE_PATH": "/custom/path/metrics.db"}
        with patch.dict(environ, environment, clear=True):
            with self.assertRaises(ValueError) as context:
                EnvConfig()
        self.assertIn("LOG_FILE_PATH", str(context.exception))

    def test_empty_metrics_database_path_raises_value_error(self):
        environment = {
            "METRICS_DATABASE_PATH": "",
            "LOG_FILE_PATH": "/custom/path/silvina.log",
        }
        with patch.dict(environ, environment, clear=True):
            with self.assertRaises(ValueError) as context:
                EnvConfig()
        self.assertIn("METRICS_DATABASE_PATH", str(context.exception))

    def test_whitespace_metrics_database_path_raises_value_error(self):
        environment = {
            "METRICS_DATABASE_PATH": "   ",
            "LOG_FILE_PATH": "/custom/path/silvina.log",
        }
        with patch.dict(environ, environment, clear=True):
            with self.assertRaises(ValueError) as context:
                EnvConfig()
        self.assertIn("METRICS_DATABASE_PATH", str(context.exception))

    def test_empty_log_file_path_raises_value_error(self):
        environment = {
            "METRICS_DATABASE_PATH": "/custom/path/metrics.db",
            "LOG_FILE_PATH": "",
        }
        with patch.dict(environ, environment, clear=True):
            with self.assertRaises(ValueError) as context:
                EnvConfig()
        self.assertIn("LOG_FILE_PATH", str(context.exception))

    def test_whitespace_log_file_path_raises_value_error(self):
        environment = {
            "METRICS_DATABASE_PATH": "/custom/path/metrics.db",
            "LOG_FILE_PATH": "   ",
        }
        with patch.dict(environ, environment, clear=True):
            with self.assertRaises(ValueError) as context:
                EnvConfig()
        self.assertIn("LOG_FILE_PATH", str(context.exception))

    def test_configured_required_paths_are_stripped_and_returned(self):
        environment = {
            "METRICS_DATABASE_PATH": "  /custom/path/metrics.db  ",
            "LOG_FILE_PATH": "  /custom/path/silvina.log  ",
        }
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
