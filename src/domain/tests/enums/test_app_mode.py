from unittest import TestCase

from src.domain.enums.app_mode import AppMode


class TestAppMode(TestCase):
    def test_members_and_values(self):
        self.assertEqual(AppMode.DEBUG.value, "DEBUG")
        self.assertEqual(AppMode.PROD.value, "PROD")

    def test_lookup_by_value(self):
        self.assertIs(AppMode("DEBUG"), AppMode.DEBUG)
        self.assertIs(AppMode("PROD"), AppMode.PROD)

    def test_invalid_value_raises_value_error(self):
        with self.assertRaises(ValueError):
            AppMode("INVALID")

    def test_member_count(self):
        self.assertEqual(len(AppMode), 2)
