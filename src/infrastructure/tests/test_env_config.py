from os import environ
from unittest import TestCase
from unittest.mock import patch

from src.domain.dtos.recommendation_settings_dto import RecommendationSettingsDTO
from src.infrastructure.env_config import EnvConfig


class TestEnvConfig(TestCase):
    def test_defaults_are_loaded_when_env_is_empty(self) -> None:
        with patch.dict(environ, {}, clear=True):
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
        self.assertFalse(config.ollama_think)
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

    def test_raises_file_not_found_when_version_file_missing_outside_testing(self):
        with patch.dict(environ, {}, clear=True):
            with patch("pathlib.Path.read_text", side_effect=FileNotFoundError):
                with self.assertRaises(FileNotFoundError):
                    EnvConfig()

    def test_testing_mode_falls_back_to_silvina_version_env_var(self):
        with patch.dict(environ, {"TESTING": "True", "SILVINA_VERSION": "0.99"}):
            with patch("pathlib.Path.read_text", side_effect=FileNotFoundError):
                config = EnvConfig()
        self.assertEqual(config.silvina_version, "0.99")

    def test_testing_mode_uses_default_version_when_silvina_version_unset(self):
        with patch.dict(environ, {"TESTING": "True"}, clear=True):
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
        invalid_values = ["yes", "1", ""]
        for invalid_value in invalid_values:
            with self.subTest(invalid_value=invalid_value):
                with patch.dict(environ, {"OLLAMA_THINK": invalid_value}):
                    with self.assertRaises(ValueError) as context:
                        EnvConfig()
                    self.assertIn("OLLAMA_THINK", str(context.exception))

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
        with patch.dict(environ, {}, clear=True):
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
