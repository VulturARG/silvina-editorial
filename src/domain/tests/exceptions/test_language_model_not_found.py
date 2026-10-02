from unittest import TestCase

from src.domain.exceptions.base_src_error import BaseSrcError
from src.domain.exceptions.language_model_errors import (
    LanguageModelError,
    LanguageModelNotFound,
    LanguageModelUnavailable,
)


class TestLanguageModelNotFound(TestCase):
    """Unit tests for the LanguageModelNotFound exception."""

    def test_is_subclass_of_language_model_error(self) -> None:
        self.assertTrue(issubclass(LanguageModelNotFound, LanguageModelError))

    def test_is_catchable_as_base_src_error(self) -> None:
        with self.assertRaises(BaseSrcError):
            raise LanguageModelNotFound()

    def test_message_is_not_empty(self) -> None:
        message = LanguageModelNotFound.MESSAGE
        self.assertIsInstance(message, str)
        assert isinstance(message, str)
        self.assertGreater(len(message), 0)

    def test_message_is_distinct_from_unavailable_message(self) -> None:
        self.assertNotEqual(LanguageModelNotFound.MESSAGE, LanguageModelUnavailable.MESSAGE)

    def test_dict_error_equals_message(self) -> None:
        error = LanguageModelNotFound()
        self.assertEqual(error.dict()["error"], LanguageModelNotFound.MESSAGE)
