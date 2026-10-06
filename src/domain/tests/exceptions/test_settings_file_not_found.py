from unittest import TestCase

from src.domain.exceptions.base_src_error import BaseSrcError
from src.domain.exceptions.settings_errors import SettingsFileNotFound, SettingsError


class TestSettingsFileNotFound(TestCase):
    def test_is_subclass_of_settings_error(self):
        self.assertTrue(issubclass(SettingsFileNotFound, SettingsError))

    def test_is_catchable_as_base_src_error(self):
        with self.assertRaises(BaseSrcError):
            raise SettingsFileNotFound("detail")

    def test_message_content(self):
        self.assertEqual(SettingsFileNotFound.MESSAGE, "The settings file could not be found.")

    def test_dict_contains_message_and_detail(self):
        self.assertEqual(
            SettingsFileNotFound("detail").dict(),
            {"error": "The settings file could not be found. detail"},
        )

    def test_exposes_the_detail(self):
        self.assertEqual(SettingsFileNotFound("detail").detail, "detail")
