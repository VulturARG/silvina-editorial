from os import environ
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from src.domain.exceptions.settings_errors import SettingsFileNotFound, SettingValueMissing
from src.infrastructure.env_config import EnvConfig

PROJECT_SETTINGS_FILE_PATH = Path(__file__).resolve().parents[3] / "settings.toml"


class TestEnvConfigSettingsFile(TestCase):
    REQUIRED_ENVIRONMENT = {
        "METRICS_DATABASE_PATH": "/custom/path/metrics.db",
        "LOG_FILE_PATH": "/custom/path/silvina.log",
    }

    def setUp(self):
        self._temporary_directory = TemporaryDirectory()
        self.addCleanup(self._temporary_directory.cleanup)
        self._settings_file_path = Path(self._temporary_directory.name) / "settings.toml"

    def _write_project_settings_with(self, original_line: str, replacement_line: str) -> None:
        project_settings = PROJECT_SETTINGS_FILE_PATH.read_text(encoding="utf-8")
        self.assertIn(original_line, project_settings)
        self._settings_file_path.write_text(
            project_settings.replace(original_line, replacement_line), encoding="utf-8"
        )

    def test_project_settings_file_provides_the_grammar_structure_and_citation_values(self):
        with patch.dict(environ, self.REQUIRED_ENVIRONMENT, clear=True):
            config = EnvConfig()

        self.assertEqual(config.grammar_max_replacements, 3)
        self.assertEqual(config.grammar_max_paragraphs, 20)
        self.assertEqual(config.grammar_max_chars, 5000)
        self.assertEqual(config.grammar_max_errors, 10)
        self.assertEqual(config.structure_max_header_length, 100)
        self.assertEqual(config.citation_max_author_name_length, 100)

    def test_project_settings_file_provides_the_article_classification_and_size_values(self):
        with patch.dict(environ, self.REQUIRED_ENVIRONMENT, clear=True):
            config = EnvConfig()

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

    def test_float_value_comes_from_the_given_settings_file(self):
        self._write_project_settings_with("temperature = 0.1", "temperature = 0.4")

        with patch.dict(environ, self.REQUIRED_ENVIRONMENT, clear=True):
            config = EnvConfig(settings_file_path=self._settings_file_path)

        self.assertAlmostEqual(config.article_classifier_temperature, 0.4)

    def test_environment_variable_overrides_the_article_size_setting(self):
        self._write_project_settings_with("long_max_chars = 40000", "long_max_chars = 50000")
        environment = {**self.REQUIRED_ENVIRONMENT, "ARTICLE_SIZE_LONG_MAX_CHARS": "45000"}

        with patch.dict(environ, environment, clear=True):
            config = EnvConfig(settings_file_path=self._settings_file_path)

        self.assertEqual(config.article_size_long_max_chars, 45000)

    def test_project_settings_file_provides_the_quality_values(self):
        with patch.dict(environ, self.REQUIRED_ENVIRONMENT, clear=True):
            config = EnvConfig()

        self.assertAlmostEqual(config.quality_level_excellent_threshold, 9.0)
        self.assertAlmostEqual(config.quality_level_good_threshold, 7.0)
        self.assertAlmostEqual(config.quality_level_acceptable_threshold, 5.0)
        self.assertAlmostEqual(config.quality_level_needs_improvement_threshold, 3.0)
        self.assertEqual(config.quality_min_sample_word_count, 10000)
        self.assertEqual(config.quality_text_sample_character_limit, 32000)
        self.assertEqual(config.quality_text_sample_reference_line_prefix_length, 80)
        self.assertEqual(config.quality_text_sample_introduction_paragraph_count, 3)
        self.assertEqual(config.quality_text_sample_middle_paragraph_count, 2)
        self.assertEqual(config.quality_text_sample_conclusion_paragraph_limit, 3)
        self.assertEqual(config.quality_text_sample_fallback_tail_paragraph_count, 2)
        self.assertEqual(config.quality_text_sample_conclusion_header_marker, "conclusi")

    def test_string_value_comes_from_the_given_settings_file(self):
        self._write_project_settings_with(
            'conclusion_header_marker = "conclusi"', 'conclusion_header_marker = "cierre"'
        )

        with patch.dict(environ, self.REQUIRED_ENVIRONMENT, clear=True):
            config = EnvConfig(settings_file_path=self._settings_file_path)

        self.assertEqual(config.quality_text_sample_conclusion_header_marker, "cierre")

    def test_environment_variable_overrides_the_quality_level_threshold(self):
        self._write_project_settings_with("good_threshold = 7.0", "good_threshold = 6.5")
        environment = {**self.REQUIRED_ENVIRONMENT, "QUALITY_LEVEL_GOOD_THRESHOLD": "8.0"}

        with patch.dict(environ, environment, clear=True):
            config = EnvConfig(settings_file_path=self._settings_file_path)

        self.assertAlmostEqual(config.quality_level_good_threshold, 8.0)

    def test_project_settings_file_provides_the_recommendation_values(self):
        with patch.dict(environ, self.REQUIRED_ENVIRONMENT, clear=True):
            config = EnvConfig()

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

    def test_recommendation_values_come_from_the_given_settings_file(self):
        self._write_project_settings_with(
            "critical_grammar_threshold = 5.0", "critical_grammar_threshold = 4.5"
        )

        with patch.dict(environ, self.REQUIRED_ENVIRONMENT, clear=True):
            config = EnvConfig(settings_file_path=self._settings_file_path)

        self.assertAlmostEqual(config.critical_grammar_threshold, 4.5)

    def test_recommendation_count_comes_from_the_given_settings_file(self):
        self._write_project_settings_with(
            "citation_count_threshold = 10", "citation_count_threshold = 12"
        )

        with patch.dict(environ, self.REQUIRED_ENVIRONMENT, clear=True):
            config = EnvConfig(settings_file_path=self._settings_file_path)

        self.assertEqual(config.citation_count_threshold, 12)

    def test_value_comes_from_the_given_settings_file(self):
        self._write_project_settings_with("max_paragraphs = 20", "max_paragraphs = 7")

        with patch.dict(environ, self.REQUIRED_ENVIRONMENT, clear=True):
            config = EnvConfig(settings_file_path=self._settings_file_path)

        self.assertEqual(config.grammar_max_paragraphs, 7)

    def test_environment_variable_overrides_the_settings_file(self):
        self._write_project_settings_with("max_paragraphs = 20", "max_paragraphs = 7")
        environment = {**self.REQUIRED_ENVIRONMENT, "GRAMMAR_MAX_PARAGRAPHS": "42"}

        with patch.dict(environ, environment, clear=True):
            config = EnvConfig(settings_file_path=self._settings_file_path)

        self.assertEqual(config.grammar_max_paragraphs, 42)

    def test_raises_setting_value_missing_naming_the_missing_key(self):
        self._write_project_settings_with("max_paragraphs = 20\n", "")

        with patch.dict(environ, self.REQUIRED_ENVIRONMENT, clear=True):
            with self.assertRaisesRegex(SettingValueMissing, "max_paragraphs"):
                EnvConfig(settings_file_path=self._settings_file_path)

    def test_raises_settings_file_not_found_when_the_settings_file_does_not_exist(self):
        with patch.dict(environ, self.REQUIRED_ENVIRONMENT, clear=True):
            with self.assertRaises(SettingsFileNotFound):
                EnvConfig(settings_file_path=self._settings_file_path)
