from unittest import TestCase

from src.domain.exceptions.base_src_error import BaseSrcError
from src.domain.exceptions.settings_errors import SettingsFileInvalid, SettingsError


class TestSettingsFileInvalid(TestCase):
    def test_is_subclass_of_settings_error(self):
        self.assertTrue(issubclass(SettingsFileInvalid, SettingsError))

    def test_is_catchable_as_base_src_error(self):
        with self.assertRaises(BaseSrcError):
            raise SettingsFileInvalid("detail")

    def test_message_content(self):
        self.assertEqual(SettingsFileInvalid.MESSAGE, "The settings file is not valid TOML.")

    def test_dict_contains_message_and_detail(self):
        self.assertEqual(
            SettingsFileInvalid("detail").dict(),
            {"error": "The settings file is not valid TOML. detail"},
        )

    def test_exposes_the_detail(self):
        self.assertEqual(SettingsFileInvalid("detail").detail, "detail")
