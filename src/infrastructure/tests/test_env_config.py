from os import environ
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from src.domain.dtos.classification_text_sampling_settings_dto import (
    ClassificationTextSamplingSettingsDTO,
)
from src.domain.dtos.quality_text_sampling_settings_dto import (
    QualityTextSamplingSettingsDTO,
)
from src.domain.dtos.recommendation_settings_dto import RecommendationSettingsDTO
from src.domain.enums.ai_provider import AiProvider
from src.domain.enums.app_mode import AppMode
from src.infrastructure.adapters.grammar.language_tool_settings import (
    LanguageToolSettings,
)
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
        self.assertEqual(config.grammar_max_paragraphs, 20)
        self.assertEqual(config.grammar_max_chars, 5000)
        self.assertEqual(config.grammar_max_errors, 10)
        self.assertEqual(config.structure_max_header_length, 100)
        self.assertAlmostEqual(config.article_classifier_temperature, 0.1)
        self.assertEqual(config.article_classifier_num_predict, 300)
        self.assertEqual(config.article_classification_sample_introduction_character_limit, 32000)
        self.assertEqual(config.article_classification_sample_conclusion_character_limit, 2500)
        self.assertEqual(config.article_classification_sample_fallback_character_limit, 6000)
        self.assertEqual(config.article_classification_bibliography_header_max_length, 30)
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
        self.assertEqual(config.quality_text_sample_reference_line_prefix_length, 80)
        self.assertEqual(config.quality_text_sample_introduction_paragraph_count, 3)
        self.assertEqual(config.quality_text_sample_middle_paragraph_count, 2)
        self.assertEqual(config.quality_text_sample_conclusion_paragraph_limit, 3)
        self.assertEqual(config.quality_text_sample_fallback_tail_paragraph_count, 2)
        self.assertEqual(config.quality_text_sample_conclusion_header_marker, "conclusi")
        self.assertEqual(config.ollama_model_name, "gemma4-26b-adapted")
        self.assertEqual(config.ollama_base_url, "http://localhost:11434")
        self.assertFalse(config.ollama_think)
        self.assertEqual(config.ollama_model_keep_alive, "15m")
        self.assertIsNone(config.ollama_num_ctx)
        self.assertTrue(config.ollama_warmup_on_startup)
        self.assertFalse(config.external_llm_think)
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
        self.assertAlmostEqual(config.report_score_high_threshold, 8.0)
        self.assertAlmostEqual(config.report_score_medium_threshold, 6.0)
        self.assertEqual(config.report_words_per_page, 250)
        self.assertEqual(config.report_max_errors_displayed, 5)
        self.assertEqual(config.report_context_truncation_limit, 150)
        self.assertEqual(config.report_max_replacements, 3)
        self.assertEqual(config.upload_max_size_bytes, 26214400)
        self.assertFalse(config.use_external_llm)
        self.assertEqual(config.app_mode, AppMode.PROD)
        self.assertEqual(config.llm_provider, AiProvider.OLLAMA)
        self.assertIsNone(config.external_llm_model_name)
        self.assertEqual(config.metrics_database_path, "/custom/path/metrics.db")
        self.assertEqual(config.log_file_path, "/custom/path/silvina.log")
        self.assertEqual(config.log_level, "INFO")
        self.assertEqual(config.log_retention_days, 14)

    def test_reads_version_from_the_version_file_outside_testing_mode(self):
        with TemporaryDirectory() as directory:
            version_file = Path(directory) / "version.txt"
            version_file.write_text("1.2.3\n", encoding="utf-8")
            with patch.dict(environ, self.REQUIRED_ENVIRONMENT, clear=True):
                with patch("src.infrastructure.env_config._VERSION_FILE_PATH", version_file):
                    config = EnvConfig()

        self.assertEqual(config.silvina_version, "1.2.3")

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

    def test_env_var_overrides_grammar_max_paragraphs(self):
        with patch.dict(environ, {"GRAMMAR_MAX_PARAGRAPHS": "25"}):
            config = EnvConfig()
        self.assertEqual(config.grammar_max_paragraphs, 25)

    def test_env_var_overrides_grammar_max_chars(self):
        with patch.dict(environ, {"GRAMMAR_MAX_CHARS": "6000"}):
            config = EnvConfig()
        self.assertEqual(config.grammar_max_chars, 6000)

    def test_env_var_overrides_grammar_max_errors(self):
        with patch.dict(environ, {"GRAMMAR_MAX_ERRORS": "15"}):
            config = EnvConfig()
        self.assertEqual(config.grammar_max_errors, 15)

    def test_env_var_overrides_structure_max_header_length(self):
        with patch.dict(environ, {"STRUCTURE_MAX_HEADER_LENGTH": "42"}):
            config = EnvConfig()
        self.assertEqual(config.structure_max_header_length, 42)

    def test_env_var_overrides_article_classifier_temperature(self):
        with patch.dict(environ, {"ARTICLE_CLASSIFIER_TEMPERATURE": "0.5"}):
            config = EnvConfig()
        self.assertAlmostEqual(config.article_classifier_temperature, 0.5)

    def test_env_var_overrides_article_classification_sample_introduction_character_limit(self):
        with patch.dict(
            environ, {"ARTICLE_CLASSIFICATION_SAMPLE_INTRODUCTION_CHARACTER_LIMIT": "4000"}
        ):
            config = EnvConfig()
        self.assertEqual(config.article_classification_sample_introduction_character_limit, 4000)

    def test_env_var_overrides_article_classification_sample_conclusion_character_limit(self):
        with patch.dict(
            environ, {"ARTICLE_CLASSIFICATION_SAMPLE_CONCLUSION_CHARACTER_LIMIT": "3000"}
        ):
            config = EnvConfig()
        self.assertEqual(config.article_classification_sample_conclusion_character_limit, 3000)

    def test_env_var_overrides_article_classification_sample_fallback_character_limit(self):
        with patch.dict(
            environ, {"ARTICLE_CLASSIFICATION_SAMPLE_FALLBACK_CHARACTER_LIMIT": "7000"}
        ):
            config = EnvConfig()
        self.assertEqual(config.article_classification_sample_fallback_character_limit, 7000)

    def test_env_var_overrides_article_classification_bibliography_header_max_length(self):
        with patch.dict(environ, {"ARTICLE_CLASSIFICATION_BIBLIOGRAPHY_HEADER_MAX_LENGTH": "40"}):
            config = EnvConfig()
        self.assertEqual(config.article_classification_bibliography_header_max_length, 40)

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
        rejected_values = ["", "  ", "15", "-1", "15min", "abc"]
        for rejected_value in rejected_values:
            with self.subTest(rejected_value=rejected_value):
                with patch.dict(environ, {"OLLAMA_MODEL_KEEP_ALIVE": rejected_value}):
                    with self.assertRaises(ValueError) as context:
                        EnvConfig()
                    self.assertIn("OLLAMA_MODEL_KEEP_ALIVE", str(context.exception))

    def test_default_ollama_num_ctx_when_env_var_absent(self):
        env_without = {k: v for k, v in environ.items() if k != "OLLAMA_NUM_CTX"}
        with patch.dict(environ, env_without, clear=True):
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
        invalid_values = ["yes", "1", ""]
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
        invalid_values = ["yes", "1", ""]
        for invalid_value in invalid_values:
            with self.subTest(invalid_value=invalid_value):
                with patch.dict(environ, {"EXTERNAL_LLM_THINK": invalid_value}):
                    with self.assertRaises(ValueError) as context:
                        EnvConfig()
                    self.assertIn("EXTERNAL_LLM_THINK", str(context.exception))

    def test_external_llm_think_is_parsed_even_when_external_llm_is_inactive(self):
        environment = {
            **self.REQUIRED_ENVIRONMENT,
            "APP_MODE": "PROD",
            "USE_EXTERNAL_LLM": "false",
            "EXTERNAL_LLM_THINK": "true",
        }
        with patch.dict(environ, environment, clear=True):
            config = EnvConfig()
        self.assertTrue(config.external_llm_think)

    def test_env_var_overrides_quality_text_sample_reference_line_prefix_length(self):
        with patch.dict(environ, {"QUALITY_TEXT_SAMPLE_REFERENCE_LINE_PREFIX_LENGTH": "120"}):
            config = EnvConfig()
        self.assertEqual(config.quality_text_sample_reference_line_prefix_length, 120)

    def test_env_var_overrides_quality_text_sample_introduction_paragraph_count(self):
        with patch.dict(environ, {"QUALITY_TEXT_SAMPLE_INTRODUCTION_PARAGRAPH_COUNT": "5"}):
            config = EnvConfig()
        self.assertEqual(config.quality_text_sample_introduction_paragraph_count, 5)

    def test_env_var_overrides_quality_text_sample_middle_paragraph_count(self):
        with patch.dict(environ, {"QUALITY_TEXT_SAMPLE_MIDDLE_PARAGRAPH_COUNT": "4"}):
            config = EnvConfig()
        self.assertEqual(config.quality_text_sample_middle_paragraph_count, 4)

    def test_env_var_overrides_quality_text_sample_conclusion_paragraph_limit(self):
        with patch.dict(environ, {"QUALITY_TEXT_SAMPLE_CONCLUSION_PARAGRAPH_LIMIT": "6"}):
            config = EnvConfig()
        self.assertEqual(config.quality_text_sample_conclusion_paragraph_limit, 6)

    def test_env_var_overrides_quality_text_sample_fallback_tail_paragraph_count(self):
        with patch.dict(environ, {"QUALITY_TEXT_SAMPLE_FALLBACK_TAIL_PARAGRAPH_COUNT": "4"}):
            config = EnvConfig()
        self.assertEqual(config.quality_text_sample_fallback_tail_paragraph_count, 4)

    def test_env_var_overrides_quality_text_sample_conclusion_header_marker(self):
        with patch.dict(environ, {"QUALITY_TEXT_SAMPLE_CONCLUSION_HEADER_MARKER": "cierre"}):
            config = EnvConfig()
        self.assertEqual(config.quality_text_sample_conclusion_header_marker, "cierre")

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

    def test_get_quality_text_sampling_settings_returns_dto_with_defaults(self):
        with patch.dict(environ, self.REQUIRED_ENVIRONMENT, clear=True):
            config = EnvConfig()
            settings = config.get_quality_text_sampling_settings()

        self.assertIsInstance(settings, QualityTextSamplingSettingsDTO)
        self.assertEqual(settings.min_sample_word_count, 400)
        self.assertEqual(settings.text_sample_character_limit, 8000)
        self.assertEqual(settings.reference_line_prefix_length, 80)
        self.assertEqual(settings.introduction_paragraph_count, 3)
        self.assertEqual(settings.middle_paragraph_count, 2)
        self.assertEqual(settings.conclusion_paragraph_limit, 3)
        self.assertEqual(settings.fallback_tail_paragraph_count, 2)
        self.assertEqual(settings.conclusion_header_marker, "conclusi")

    def test_get_quality_text_sampling_settings_reflects_env_overrides(self):
        overrides = {
            "QUALITY_MIN_SAMPLE_WORD_COUNT": "500",
            "QUALITY_TEXT_SAMPLE_CHARACTER_LIMIT": "9000",
            "QUALITY_TEXT_SAMPLE_REFERENCE_LINE_PREFIX_LENGTH": "90",
            "QUALITY_TEXT_SAMPLE_INTRODUCTION_PARAGRAPH_COUNT": "4",
            "QUALITY_TEXT_SAMPLE_MIDDLE_PARAGRAPH_COUNT": "3",
            "QUALITY_TEXT_SAMPLE_CONCLUSION_PARAGRAPH_LIMIT": "5",
            "QUALITY_TEXT_SAMPLE_FALLBACK_TAIL_PARAGRAPH_COUNT": "3",
            "QUALITY_TEXT_SAMPLE_CONCLUSION_HEADER_MARKER": "cierre",
        }
        with patch.dict(environ, overrides):
            settings = EnvConfig().get_quality_text_sampling_settings()

        self.assertEqual(settings.min_sample_word_count, 500)
        self.assertEqual(settings.text_sample_character_limit, 9000)
        self.assertEqual(settings.reference_line_prefix_length, 90)
        self.assertEqual(settings.introduction_paragraph_count, 4)
        self.assertEqual(settings.middle_paragraph_count, 3)
        self.assertEqual(settings.conclusion_paragraph_limit, 5)
        self.assertEqual(settings.fallback_tail_paragraph_count, 3)
        self.assertEqual(settings.conclusion_header_marker, "cierre")

    def test_get_classification_text_sampling_settings_returns_dto_with_defaults(self):
        with patch.dict(environ, self.REQUIRED_ENVIRONMENT, clear=True):
            settings = EnvConfig().get_classification_text_sampling_settings()

        self.assertIsInstance(settings, ClassificationTextSamplingSettingsDTO)
        self.assertEqual(settings.introduction_character_limit, 32000)
        self.assertEqual(settings.conclusion_character_limit, 2500)
        self.assertEqual(settings.fallback_character_limit, 6000)
        self.assertEqual(settings.bibliography_header_max_length, 30)

    def test_get_classification_text_sampling_settings_reflects_env_overrides(self):
        overrides = {
            "ARTICLE_CLASSIFICATION_SAMPLE_INTRODUCTION_CHARACTER_LIMIT": "4000",
            "ARTICLE_CLASSIFICATION_SAMPLE_CONCLUSION_CHARACTER_LIMIT": "3000",
            "ARTICLE_CLASSIFICATION_SAMPLE_FALLBACK_CHARACTER_LIMIT": "7000",
            "ARTICLE_CLASSIFICATION_BIBLIOGRAPHY_HEADER_MAX_LENGTH": "40",
        }
        with patch.dict(environ, overrides):
            settings = EnvConfig().get_classification_text_sampling_settings()

        self.assertEqual(settings.introduction_character_limit, 4000)
        self.assertEqual(settings.conclusion_character_limit, 3000)
        self.assertEqual(settings.fallback_character_limit, 7000)
        self.assertEqual(settings.bibliography_header_max_length, 40)

    def test_get_language_tool_settings_returns_settings_with_defaults(self):
        with patch.dict(environ, self.REQUIRED_ENVIRONMENT, clear=True):
            settings = EnvConfig().get_language_tool_settings()

        self.assertIsInstance(settings, LanguageToolSettings)
        self.assertEqual(settings.max_replacements, 3)
        self.assertEqual(settings.max_paragraphs, 20)
        self.assertEqual(settings.max_chars, 5000)
        self.assertEqual(settings.max_errors, 10)

    def test_get_language_tool_settings_reflects_env_overrides(self):
        overrides = {
            "GRAMMAR_MAX_REPLACEMENTS": "5",
            "GRAMMAR_MAX_PARAGRAPHS": "30",
            "GRAMMAR_MAX_CHARS": "8000",
            "GRAMMAR_MAX_ERRORS": "15",
        }
        with patch.dict(environ, overrides):
            settings = EnvConfig().get_language_tool_settings()

        self.assertEqual(settings.max_replacements, 5)
        self.assertEqual(settings.max_paragraphs, 30)
        self.assertEqual(settings.max_chars, 8000)
        self.assertEqual(settings.max_errors, 15)

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

    def test_llm_provider_defaults_to_ollama_when_environment_is_empty(self):
        with patch.dict(environ, self.REQUIRED_ENVIRONMENT, clear=True):
            config = EnvConfig()
        self.assertFalse(config.use_external_llm)
        self.assertEqual(config.llm_provider, AiProvider.OLLAMA)
        self.assertIsNone(config.external_llm_model_name)

    def test_use_external_llm_flag_true_in_debug_mode_with_claude_sets_attributes(self):
        environment = {
            **self.REQUIRED_ENVIRONMENT,
            "APP_MODE": "DEBUG",
            "USE_EXTERNAL_LLM": "true",
            "LLM_PROVIDER": "claude",
            "EXTERNAL_LLM_MODEL_NAME": "claude-3-5-sonnet",
        }
        with patch.dict(environ, environment, clear=True):
            config = EnvConfig()
        self.assertTrue(config.use_external_llm)
        self.assertEqual(config.llm_provider, AiProvider.CLAUDE)
        self.assertEqual(config.external_llm_model_name, "claude-3-5-sonnet")

    def test_debug_mode_with_external_llm_enabled_without_provider_raises_value_error(self):
        environment = {
            **self.REQUIRED_ENVIRONMENT,
            "APP_MODE": "DEBUG",
            "USE_EXTERNAL_LLM": "true",
            "EXTERNAL_LLM_MODEL_NAME": "claude-3-5-sonnet",
        }
        with patch.dict(environ, environment, clear=True):
            with self.assertRaises(ValueError) as context:
                EnvConfig()
        self.assertIn("LLM_PROVIDER", str(context.exception))

    def test_debug_mode_with_external_llm_enabled_and_blank_provider_raises_value_error(self):
        environment = {
            **self.REQUIRED_ENVIRONMENT,
            "APP_MODE": "DEBUG",
            "USE_EXTERNAL_LLM": "true",
            "LLM_PROVIDER": "   ",
            "EXTERNAL_LLM_MODEL_NAME": "claude-3-5-sonnet",
        }
        with patch.dict(environ, environment, clear=True):
            with self.assertRaises(ValueError) as context:
                EnvConfig()
        self.assertIn("LLM_PROVIDER", str(context.exception))

    def test_debug_mode_with_external_llm_enabled_and_ollama_provider_raises_value_error(self):
        environment = {
            **self.REQUIRED_ENVIRONMENT,
            "APP_MODE": "DEBUG",
            "USE_EXTERNAL_LLM": "true",
            "LLM_PROVIDER": "ollama",
            "EXTERNAL_LLM_MODEL_NAME": "claude-3-5-sonnet",
        }
        with patch.dict(environ, environment, clear=True):
            with self.assertRaises(ValueError) as context:
                EnvConfig()
        self.assertIn("LLM_PROVIDER", str(context.exception))
        self.assertIn("claude", str(context.exception).lower())

    def test_debug_mode_with_external_llm_enabled_without_model_raises_value_error(self):
        environment = {
            **self.REQUIRED_ENVIRONMENT,
            "APP_MODE": "DEBUG",
            "USE_EXTERNAL_LLM": "true",
            "LLM_PROVIDER": "claude",
        }
        with patch.dict(environ, environment, clear=True):
            with self.assertRaises(ValueError) as context:
                EnvConfig()
        self.assertIn("EXTERNAL_LLM_MODEL_NAME", str(context.exception))

    def test_debug_mode_with_external_llm_enabled_and_blank_model_raises_value_error(self):
        environment = {
            **self.REQUIRED_ENVIRONMENT,
            "APP_MODE": "DEBUG",
            "USE_EXTERNAL_LLM": "true",
            "LLM_PROVIDER": "claude",
            "EXTERNAL_LLM_MODEL_NAME": "   ",
        }
        with patch.dict(environ, environment, clear=True):
            with self.assertRaises(ValueError) as context:
                EnvConfig()
        self.assertIn("EXTERNAL_LLM_MODEL_NAME", str(context.exception))

    def test_prod_mode_with_external_llm_flag_true_uses_ollama_and_ignores_provider_and_model(self):
        environment = {
            **self.REQUIRED_ENVIRONMENT,
            "APP_MODE": "PROD",
            "USE_EXTERNAL_LLM": "true",
            "LLM_PROVIDER": "invalid_provider",
            "EXTERNAL_LLM_MODEL_NAME": "   ",
        }
        with patch.dict(environ, environment, clear=True):
            config = EnvConfig()
        self.assertTrue(config.use_external_llm)
        self.assertEqual(config.llm_provider, AiProvider.OLLAMA)
        self.assertIsNone(config.external_llm_model_name)

    def test_debug_mode_with_external_llm_flag_false_ignores_invalid_provider_without_raising(self):
        environment = {
            **self.REQUIRED_ENVIRONMENT,
            "APP_MODE": "DEBUG",
            "USE_EXTERNAL_LLM": "false",
            "LLM_PROVIDER": "invalid_provider",
        }
        with patch.dict(environ, environment, clear=True):
            config = EnvConfig()
        self.assertFalse(config.use_external_llm)
        self.assertEqual(config.llm_provider, AiProvider.OLLAMA)
        self.assertIsNone(config.external_llm_model_name)

    def test_debug_mode_with_external_llm_flag_false_and_claude_set_uses_ollama_and_none_model(
        self,
    ):
        environment = {
            **self.REQUIRED_ENVIRONMENT,
            "APP_MODE": "DEBUG",
            "USE_EXTERNAL_LLM": "false",
            "LLM_PROVIDER": "claude",
            "EXTERNAL_LLM_MODEL_NAME": "claude-3-5-sonnet",
        }
        with patch.dict(environ, environment, clear=True):
            config = EnvConfig()
        self.assertFalse(config.use_external_llm)
        self.assertEqual(config.llm_provider, AiProvider.OLLAMA)
        self.assertIsNone(config.external_llm_model_name)

    def test_invalid_use_external_llm_value_raises_value_error(self):
        invalid_values = ["yes", "1", "disabled", ""]
        for invalid_value in invalid_values:
            with self.subTest(invalid_value=invalid_value):
                environment = {
                    **self.REQUIRED_ENVIRONMENT,
                    "USE_EXTERNAL_LLM": invalid_value,
                }
                with patch.dict(environ, environment, clear=True):
                    with self.assertRaises(ValueError) as context:
                        EnvConfig()
                    self.assertIn("USE_EXTERNAL_LLM", str(context.exception))

    def test_external_llm_provider_accepts_case_and_whitespace_variations(self):
        environment = {
            **self.REQUIRED_ENVIRONMENT,
            "APP_MODE": "DEBUG",
            "USE_EXTERNAL_LLM": "true",
            "LLM_PROVIDER": "  CLAUDE  ",
            "EXTERNAL_LLM_MODEL_NAME": "claude-3-5-sonnet",
        }
        with patch.dict(environ, environment, clear=True):
            config = EnvConfig()
        self.assertEqual(config.llm_provider, AiProvider.CLAUDE)

    def test_invalid_external_llm_provider_raises_value_error_listing_accepted_providers(self):
        environment = {
            **self.REQUIRED_ENVIRONMENT,
            "APP_MODE": "DEBUG",
            "USE_EXTERNAL_LLM": "true",
            "LLM_PROVIDER": "invalid_provider",
            "EXTERNAL_LLM_MODEL_NAME": "claude-3-5-sonnet",
        }
        with patch.dict(environ, environment, clear=True):
            with self.assertRaises(ValueError) as context:
                EnvConfig()
        self.assertIn("LLM_PROVIDER", str(context.exception))
        self.assertIn("claude", str(context.exception).lower())

    def test_external_llm_model_name_is_stripped_when_provided(self):
        environment = {
            **self.REQUIRED_ENVIRONMENT,
            "APP_MODE": "DEBUG",
            "USE_EXTERNAL_LLM": "true",
            "LLM_PROVIDER": "claude",
            "EXTERNAL_LLM_MODEL_NAME": "  claude-3-5-sonnet  ",
        }
        with patch.dict(environ, environment, clear=True):
            config = EnvConfig()
        self.assertEqual(config.external_llm_model_name, "claude-3-5-sonnet")

    def test_blank_external_llm_model_name_evaluates_to_none_when_external_llm_inactive(self):
        environment = {
            **self.REQUIRED_ENVIRONMENT,
            "USE_EXTERNAL_LLM": "false",
            "EXTERNAL_LLM_MODEL_NAME": "   ",
        }
        with patch.dict(environ, environment, clear=True):
            config = EnvConfig()
        self.assertIsNone(config.external_llm_model_name)
