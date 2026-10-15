from unittest import TestCase

from src.domain.exceptions.base_src_error import BaseSrcError
from src.domain.exceptions.language_model_errors import (
    LanguageModelError,
    LanguageModelServerExecutableNotFound,
    LanguageModelServerStartFailed,
)


class TestLanguageModelServerExecutableNotFound(TestCase):
    """Unit tests for the LanguageModelServerExecutableNotFound exception."""

    def test_is_subclass_of_language_model_server_start_failed(self) -> None:
        self.assertTrue(
            issubclass(LanguageModelServerExecutableNotFound, LanguageModelServerStartFailed)
        )
        self.assertTrue(issubclass(LanguageModelServerExecutableNotFound, LanguageModelError))

    def test_is_catchable_as_base_src_error(self) -> None:
        with self.assertRaises(BaseSrcError):
            raise LanguageModelServerExecutableNotFound()

    def test_message_is_not_empty(self) -> None:
        message = LanguageModelServerExecutableNotFound.MESSAGE
        self.assertIsInstance(message, str)
        self.assertGreater(len(message), 0)

    def test_dict_error_equals_message(self) -> None:
        error = LanguageModelServerExecutableNotFound()
        self.assertEqual(error.dict()["error"], LanguageModelServerExecutableNotFound.MESSAGE)
