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
