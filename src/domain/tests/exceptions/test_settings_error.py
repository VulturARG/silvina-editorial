from unittest import TestCase

from src.domain.exceptions.base_src_error import BaseSrcError
from src.domain.exceptions.settings_errors import SettingsError


class TestSettingsError(TestCase):
    def test_is_subclass_of_base_src_error(self):
        self.assertTrue(issubclass(SettingsError, BaseSrcError))

    def test_is_catchable_as_base_src_error(self):
        with self.assertRaises(BaseSrcError):
            raise SettingsError("detail")

    def test_exposes_the_detail(self):
        self.assertEqual(SettingsError("section [grammar]").detail, "section [grammar]")

    def test_dict_appends_the_detail_to_the_message(self):
        error = SettingsError("section [grammar]")

        self.assertTrue(error.dict()["error"].endswith("section [grammar]"))

    def test_string_representation_matches_the_dict_error(self):
        error = SettingsError("section [grammar]")

        self.assertEqual(str(error), error.dict()["error"])
