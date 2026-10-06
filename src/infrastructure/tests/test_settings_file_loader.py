from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from src.domain.exceptions.settings_errors import SettingsFileInvalid, SettingsFileNotFound
from src.infrastructure.settings_file_loader import SettingsFileLoader


class TestSettingsFileLoader(TestCase):
    def setUp(self):
        self._temporary_directory = TemporaryDirectory()
        self.addCleanup(self._temporary_directory.cleanup)
        self._settings_file_path = Path(self._temporary_directory.name) / "settings.toml"

    def test_loads_sections_with_typed_values(self):
        self._settings_file_path.write_text(
            '[grammar]\nmax_errors = 10\nthreshold = 0.5\nenabled = true\nname = "text"\n',
            encoding="utf-8",
        )

        settings = SettingsFileLoader(self._settings_file_path).load()

        self.assertEqual(
            settings,
            {"grammar": {"max_errors": 10, "threshold": 0.5, "enabled": True, "name": "text"}},
        )

    def test_loads_utf8_content(self):
        self._settings_file_path.write_text('[quality]\nmarker = "conclusión"\n', encoding="utf-8")

        settings = SettingsFileLoader(self._settings_file_path).load()

        self.assertEqual(settings["quality"]["marker"], "conclusión")

    def test_raises_settings_file_not_found_naming_the_path_when_file_is_missing(self):
        loader = SettingsFileLoader(self._settings_file_path)

        with self.assertRaises(SettingsFileNotFound) as context:
            loader.load()

        self.assertIn(str(self._settings_file_path), context.exception.dict()["error"])

    def test_raises_settings_file_invalid_naming_the_path_when_toml_is_invalid(self):
        self._settings_file_path.write_text("[grammar\nmax_errors = ", encoding="utf-8")
        loader = SettingsFileLoader(self._settings_file_path)

        with self.assertRaises(SettingsFileInvalid) as context:
            loader.load()

        self.assertIn(str(self._settings_file_path), context.exception.dict()["error"])
