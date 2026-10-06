from unittest import TestCase

from src.domain.exceptions.base_src_error import BaseSrcError
from src.domain.exceptions.settings_errors import SettingValueInvalid, SettingsError


class TestSettingValueInvalid(TestCase):
    def test_is_subclass_of_settings_error(self):
        self.assertTrue(issubclass(SettingValueInvalid, SettingsError))

    def test_is_catchable_as_base_src_error(self):
        with self.assertRaises(BaseSrcError):
            raise SettingValueInvalid("detail")

    def test_message_content(self):
        self.assertEqual(SettingValueInvalid.MESSAGE, "A setting has an invalid value.")

    def test_dict_contains_message_and_detail(self):
        self.assertEqual(
            SettingValueInvalid("detail").dict(),
            {"error": "A setting has an invalid value. detail"},
        )

    def test_exposes_the_detail(self):
        self.assertEqual(SettingValueInvalid("detail").detail, "detail")
