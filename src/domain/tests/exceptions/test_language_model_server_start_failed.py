from unittest import TestCase

from src.domain.exceptions.base_src_error import BaseSrcError
from src.domain.exceptions.language_model_errors import (
    LanguageModelError,
    LanguageModelServerStartFailed,
    LanguageModelUnavailable,
)


class TestLanguageModelServerStartFailed(TestCase):
    """Unit tests for the LanguageModelServerStartFailed exception."""

    def test_is_subclass_of_language_model_error(self) -> None:
        self.assertTrue(issubclass(LanguageModelServerStartFailed, LanguageModelError))

    def test_is_catchable_as_base_src_error(self) -> None:
        with self.assertRaises(BaseSrcError):
            raise LanguageModelServerStartFailed()

    def test_message_is_not_empty(self) -> None:
        message = LanguageModelServerStartFailed.MESSAGE
        self.assertIsInstance(message, str)
        self.assertGreater(len(message), 0)

    def test_message_is_distinct_from_unavailable_message(self) -> None:
        self.assertNotEqual(
            LanguageModelServerStartFailed.MESSAGE, LanguageModelUnavailable.MESSAGE
        )

    def test_dict_error_equals_message(self) -> None:
        error = LanguageModelServerStartFailed()
        self.assertEqual(error.dict()["error"], LanguageModelServerStartFailed.MESSAGE)
