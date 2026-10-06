from unittest import TestCase

from src.domain.exceptions.base_src_error import BaseSrcError
from src.domain.exceptions.settings_errors import SettingValueMissing, SettingsError


class TestSettingValueMissing(TestCase):
    def test_is_subclass_of_settings_error(self):
        self.assertTrue(issubclass(SettingValueMissing, SettingsError))

    def test_is_catchable_as_base_src_error(self):
        with self.assertRaises(BaseSrcError):
            raise SettingValueMissing("detail")

    def test_message_content(self):
        self.assertEqual(SettingValueMissing.MESSAGE, "A required setting is missing.")

    def test_dict_contains_message_and_detail(self):
        self.assertEqual(
            SettingValueMissing("detail").dict(), {"error": "A required setting is missing. detail"}
        )

    def test_exposes_the_detail(self):
        self.assertEqual(SettingValueMissing("detail").detail, "detail")
