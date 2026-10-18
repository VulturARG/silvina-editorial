from unittest import TestCase

from src.domain.exceptions.base_src_error import BaseSrcError
from src.domain.exceptions.language_model_errors import (
    LanguageModelError,
    LanguageModelOutputTruncated,
)


class TestLanguageModelOutputTruncated(TestCase):
    """Unit tests for the LanguageModelOutputTruncated exception."""

    def test_is_subclass_of_language_model_error(self) -> None:
        self.assertTrue(issubclass(LanguageModelOutputTruncated, LanguageModelError))

    def test_is_catchable_as_base_src_error(self) -> None:
        with self.assertRaises(BaseSrcError):
            raise LanguageModelOutputTruncated()

    def test_message_names_the_output_token_limit_and_the_settings_file(self) -> None:
        message = LanguageModelOutputTruncated.MESSAGE
        self.assertIn("output token limit", message)
        self.assertIn("settings file", message)
