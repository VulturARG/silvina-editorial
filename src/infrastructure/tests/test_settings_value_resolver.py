from os import environ
from unittest import TestCase
from unittest.mock import patch

from src.domain.exceptions.settings_errors import SettingValueInvalid, SettingValueMissing
from src.infrastructure.settings_value_resolver import SettingsValueResolver


class TestSettingsValueResolver(TestCase):
    def setUp(self):
        settings = {
            "grammar": {
                "max_errors": 10,
                "threshold": 0.5,
                "whole_threshold": 7,
                "marker": "conclusi",
                "flag": True,
                "text_as_number": "10",
            }
        }
        self._resolver = SettingsValueResolver(settings)

    def test_reads_integer_from_settings_when_environment_variable_is_absent(self):
        with patch.dict(environ, {}, clear=True):
            value = self._resolver.read_integer("GRAMMAR_MAX_ERRORS", "grammar", "max_errors")

        self.assertEqual(value, 10)
        self.assertIsInstance(value, int)

    def test_environment_variable_overrides_integer_from_settings(self):
        with patch.dict(environ, {"GRAMMAR_MAX_ERRORS": "25"}, clear=True):
            value = self._resolver.read_integer("GRAMMAR_MAX_ERRORS", "grammar", "max_errors")

        self.assertEqual(value, 25)

    def test_raises_setting_value_invalid_naming_variable_when_integer_environment_variable_is_invalid(
        self,
    ):
        with patch.dict(environ, {"GRAMMAR_MAX_ERRORS": "many"}, clear=True):
            with self.assertRaisesRegex(SettingValueInvalid, "GRAMMAR_MAX_ERRORS"):
                self._resolver.read_integer("GRAMMAR_MAX_ERRORS", "grammar", "max_errors")

    def test_raises_setting_value_invalid_when_integer_setting_is_not_an_integer(self):
        with patch.dict(environ, {}, clear=True):
            with self.assertRaisesRegex(SettingValueInvalid, r"'threshold'.*\[grammar\]"):
                self._resolver.read_integer("GRAMMAR_THRESHOLD", "grammar", "threshold")

    def test_raises_setting_value_invalid_when_integer_setting_is_a_boolean(self):
        with patch.dict(environ, {}, clear=True):
            with self.assertRaisesRegex(SettingValueInvalid, r"'flag'.*\[grammar\]"):
                self._resolver.read_integer("GRAMMAR_FLAG", "grammar", "flag")

    def test_raises_setting_value_invalid_when_integer_setting_is_text(self):
        with patch.dict(environ, {}, clear=True):
            with self.assertRaisesRegex(SettingValueInvalid, r"'text_as_number'.*\[grammar\]"):
                self._resolver.read_integer("GRAMMAR_TEXT_AS_NUMBER", "grammar", "text_as_number")

    def test_reads_float_from_settings_when_environment_variable_is_absent(self):
        with patch.dict(environ, {}, clear=True):
            value = self._resolver.read_float("GRAMMAR_THRESHOLD", "grammar", "threshold")

        self.assertAlmostEqual(value, 0.5)

    def test_reads_whole_number_setting_as_float(self):
        with patch.dict(environ, {}, clear=True):
            value = self._resolver.read_float(
                "GRAMMAR_WHOLE_THRESHOLD", "grammar", "whole_threshold"
            )

        self.assertEqual(value, 7.0)
        self.assertIsInstance(value, float)

    def test_environment_variable_overrides_float_from_settings(self):
        with patch.dict(environ, {"GRAMMAR_THRESHOLD": "0.9"}, clear=True):
            value = self._resolver.read_float("GRAMMAR_THRESHOLD", "grammar", "threshold")

        self.assertAlmostEqual(value, 0.9)

    def test_raises_setting_value_invalid_naming_variable_when_float_environment_variable_is_invalid(
        self,
    ):
        with patch.dict(environ, {"GRAMMAR_THRESHOLD": "high"}, clear=True):
            with self.assertRaisesRegex(SettingValueInvalid, "GRAMMAR_THRESHOLD"):
                self._resolver.read_float("GRAMMAR_THRESHOLD", "grammar", "threshold")

    def test_raises_setting_value_invalid_when_float_setting_is_a_boolean(self):
        with patch.dict(environ, {}, clear=True):
            with self.assertRaisesRegex(SettingValueInvalid, r"'flag'.*\[grammar\]"):
                self._resolver.read_float("GRAMMAR_FLAG", "grammar", "flag")

    def test_reads_string_from_settings_when_environment_variable_is_absent(self):
        with patch.dict(environ, {}, clear=True):
            value = self._resolver.read_string("GRAMMAR_MARKER", "grammar", "marker")

        self.assertEqual(value, "conclusi")

    def test_environment_variable_overrides_string_from_settings(self):
        with patch.dict(environ, {"GRAMMAR_MARKER": "cierre"}, clear=True):
            value = self._resolver.read_string("GRAMMAR_MARKER", "grammar", "marker")

        self.assertEqual(value, "cierre")

    def test_raises_setting_value_invalid_when_string_setting_is_not_text(self):
        with patch.dict(environ, {}, clear=True):
            with self.assertRaisesRegex(SettingValueInvalid, r"'max_errors'.*\[grammar\]"):
                self._resolver.read_string("GRAMMAR_MAX_ERRORS", "grammar", "max_errors")

    def test_raises_setting_value_invalid_naming_section_key_and_variable_when_setting_is_missing(
        self,
    ):
        with patch.dict(environ, {}, clear=True):
            with self.assertRaises(SettingValueMissing) as context:
                self._resolver.read_integer("GRAMMAR_MAX_PAGES", "grammar", "max_pages")

        message = context.exception.dict()["error"]
        self.assertIn("[grammar]", message)
        self.assertIn("max_pages", message)
        self.assertIn("GRAMMAR_MAX_PAGES", message)

    def test_raises_setting_value_missing_when_section_is_missing(self):
        with patch.dict(environ, {}, clear=True):
            with self.assertRaisesRegex(SettingValueMissing, r"\[structure\]"):
                self._resolver.read_integer(
                    "STRUCTURE_MAX_HEADER_LENGTH", "structure", "max_header_length"
                )
