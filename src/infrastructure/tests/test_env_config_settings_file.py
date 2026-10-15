from os import environ
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from src.domain.dtos.recommendation_settings_dto import RecommendationSettingsDTO
from src.domain.exceptions.settings_errors import SettingsFileNotFound, SettingValueMissing
from src.infrastructure.adapters.grammar.language_tool_settings import (
    LanguageToolSettings,
)
from src.infrastructure.env_config import EnvConfig
from src.infrastructure.tests.test_doubles.complete_test_environment import (
    CompleteTestEnvironment,
)
from src.infrastructure.tests.test_doubles.complete_test_settings import (
    CompleteTestSettings,
)


class TestEnvConfigSettingsFile(TestCase):
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

    def setUp(self):
        self._temporary_directory = TemporaryDirectory()
        self.addCleanup(self._temporary_directory.cleanup)
        self._settings_file_path = Path(self._temporary_directory.name) / "settings.toml"
        self._write_settings()

    def _write_settings(self, overrides: dict[str, int | float | str | None] | None = None) -> None:
        self._settings_file_path.write_text(
            CompleteTestSettings.toml_text(overrides), encoding="utf-8"
        )

    def test_settings_file_provides_every_setting_read_from_the_file(self):
        with patch.dict(environ, self._complete_environment(), clear=True):
            config = EnvConfig(settings_file_path=self._settings_file_path)

        for attribute_name, expected_value in CompleteTestSettings.expected_values().items():
            with self.subTest(attribute_name=attribute_name):
                self.assertEqual(getattr(config, attribute_name), expected_value)

    def test_project_settings_file_provides_every_setting_with_the_expected_type(self):
        with patch.dict(environ, self._complete_environment(), clear=True):
            config = EnvConfig()

        for attribute_name, expected_value in CompleteTestSettings.expected_values().items():
            with self.subTest(attribute_name=attribute_name):
                self.assertIsInstance(getattr(config, attribute_name), type(expected_value))

    def test_get_recommendation_settings_maps_every_field_from_the_settings_file(self):
        expected = CompleteTestSettings.expected_values()
        with patch.dict(environ, self._complete_environment(), clear=True):
            config = EnvConfig(settings_file_path=self._settings_file_path)
            settings = config.get_recommendation_settings()

        self.assertIsInstance(settings, RecommendationSettingsDTO)
        self.assertEqual(settings.publish_threshold, expected["publish_threshold"])
        self.assertEqual(settings.quality_threshold, expected["quality_threshold"])
        self.assertEqual(settings.grammar_threshold, expected["grammar_threshold"])
        self.assertEqual(settings.dimension_threshold, expected["dimension_threshold"])
        self.assertEqual(settings.citation_match_threshold, expected["citation_match_threshold"])
        self.assertEqual(
            settings.critical_citation_match_threshold,
            expected["critical_citation_match_threshold"],
        )
        self.assertEqual(settings.citation_count_threshold, expected["citation_count_threshold"])
        self.assertEqual(
            settings.classification_confidence_threshold,
            expected["classification_confidence_threshold"],
        )
        self.assertEqual(
            settings.critical_quality_threshold, expected["critical_quality_threshold"]
        )
        self.assertEqual(
            settings.critical_grammar_threshold, expected["critical_grammar_threshold"]
        )

    def test_get_language_tool_settings_maps_every_field_from_the_settings_file(self):
        expected = CompleteTestSettings.expected_values()
        with patch.dict(environ, self._complete_environment(), clear=True):
            config = EnvConfig(settings_file_path=self._settings_file_path)
            settings = config.get_language_tool_settings()

        self.assertIsInstance(settings, LanguageToolSettings)
        self.assertEqual(settings.max_replacements, expected["grammar_max_replacements"])
        self.assertEqual(settings.max_paragraphs, expected["grammar_max_paragraphs"])
        self.assertEqual(settings.max_chars, expected["grammar_max_chars"])
        self.assertEqual(settings.max_errors, expected["grammar_max_errors"])

    def test_float_value_comes_from_the_given_settings_file(self):
        self._write_settings({"article_classifier_temperature": 0.4})

        with patch.dict(environ, self._complete_environment(), clear=True):
            config = EnvConfig(settings_file_path=self._settings_file_path)

        self.assertAlmostEqual(config.article_classifier_temperature, 0.4)

    def test_environment_variable_overrides_the_article_size_setting(self):
        environment = self._complete_environment({"ARTICLE_SIZE_LONG_MAX_CHARS": "45000"})

        with patch.dict(environ, environment, clear=True):
            config = EnvConfig(settings_file_path=self._settings_file_path)

        self.assertEqual(config.article_size_long_max_chars, 45000)

    def test_environment_variable_overrides_the_quality_level_threshold(self):
        environment = self._complete_environment({"QUALITY_LEVEL_GOOD_THRESHOLD": "8.0"})

        with patch.dict(environ, environment, clear=True):
            config = EnvConfig(settings_file_path=self._settings_file_path)

        self.assertAlmostEqual(config.quality_level_good_threshold, 8.0)

    def test_recommendation_values_come_from_the_given_settings_file(self):
        self._write_settings({"critical_grammar_threshold": 4.5})

        with patch.dict(environ, self._complete_environment(), clear=True):
            config = EnvConfig(settings_file_path=self._settings_file_path)

        self.assertAlmostEqual(config.critical_grammar_threshold, 4.5)

    def test_recommendation_count_comes_from_the_given_settings_file(self):
        self._write_settings({"citation_count_threshold": 12})

        with patch.dict(environ, self._complete_environment(), clear=True):
            config = EnvConfig(settings_file_path=self._settings_file_path)

        self.assertEqual(config.citation_count_threshold, 12)

    def test_upload_limit_comes_from_the_given_settings_file(self):
        self._write_settings({"upload_max_size_bytes": 1048576})

        with patch.dict(environ, self._complete_environment(), clear=True):
            config = EnvConfig(settings_file_path=self._settings_file_path)

        self.assertEqual(config.upload_max_size_bytes, 1048576)

    def test_report_threshold_comes_from_the_given_settings_file(self):
        self._write_settings({"report_score_high_threshold": 8.5})

        with patch.dict(environ, self._complete_environment(), clear=True):
            config = EnvConfig(settings_file_path=self._settings_file_path)

        self.assertAlmostEqual(config.report_score_high_threshold, 8.5)

    def test_environment_variable_overrides_the_report_words_per_page(self):
        environment = self._complete_environment({"REPORT_WORDS_PER_PAGE": "275"})

        with patch.dict(environ, environment, clear=True):
            config = EnvConfig(settings_file_path=self._settings_file_path)

        self.assertEqual(config.report_words_per_page, 275)

    def test_value_comes_from_the_given_settings_file(self):
        self._write_settings({"grammar_max_paragraphs": 7})

        with patch.dict(environ, self._complete_environment(), clear=True):
            config = EnvConfig(settings_file_path=self._settings_file_path)

        self.assertEqual(config.grammar_max_paragraphs, 7)

    def test_environment_variable_overrides_the_settings_file(self):
        environment = self._complete_environment({"GRAMMAR_MAX_PARAGRAPHS": "42"})

        with patch.dict(environ, environment, clear=True):
            config = EnvConfig(settings_file_path=self._settings_file_path)

        self.assertEqual(config.grammar_max_paragraphs, 42)

    def test_raises_setting_value_missing_naming_the_missing_key(self):
        self._write_settings({"grammar_max_paragraphs": None})

        with patch.dict(environ, self._complete_environment(), clear=True):
            with self.assertRaises(SettingValueMissing) as context:
                EnvConfig(settings_file_path=self._settings_file_path)
            self.assertRegex(context.exception.dict()["error"], "max_paragraphs")

    def test_raises_settings_file_not_found_when_the_settings_file_does_not_exist(self):
        missing_settings_file_path = Path(self._temporary_directory.name) / "missing.toml"

        with patch.dict(environ, self._complete_environment(), clear=True):
            with self.assertRaises(SettingsFileNotFound):
                EnvConfig(settings_file_path=missing_settings_file_path)

    def test_environment_variable_overrides_the_eumic_min_words_for_abstract_check_setting(self):
        environment = self._complete_environment({"EUMIC_MIN_WORDS_FOR_ABSTRACT_CHECK": "1500"})

        with patch.dict(environ, environment, clear=True):
            config = EnvConfig(settings_file_path=self._settings_file_path)

        self.assertEqual(config.eumic_min_words_for_abstract_check, 1500)
