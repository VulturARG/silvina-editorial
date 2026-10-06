from unittest import TestCase

from src.domain.exceptions.base_src_error import BaseSrcError
from src.domain.exceptions.settings_errors import SettingsError


class TestSettingsError(TestCase):
    def test_is_subclass_of_base_src_error(self):
        self.assertTrue(issubclass(SettingsError, BaseSrcError))

    def test_is_catchable_as_base_src_error(self):
        with self.assertRaises(BaseSrcError):
            raise SettingsError()

    def test_does_not_define_its_own_behaviour(self):
        for method_name in ("__init__", "dict"):
            self.assertNotIn(method_name, vars(SettingsError))
