from unittest import TestCase

from src.domain.exceptions.base_src_error import BaseSrcError
from src.domain.exceptions.language_model_errors import (
    LanguageModelBackendNotInstalled,
    LanguageModelError,
)


class TestLanguageModelBackendNotInstalled(TestCase):
    def test_is_subclass_of_language_model_error(self):
        self.assertTrue(issubclass(LanguageModelBackendNotInstalled, LanguageModelError))

    def test_is_catchable_as_base_src_error(self):
        with self.assertRaises(BaseSrcError):
            raise LanguageModelBackendNotInstalled()

    def test_message_is_not_empty(self):
        self.assertGreater(len(LanguageModelBackendNotInstalled.MESSAGE), 0)

    def test_message_mentions_requirements_debug(self):
        self.assertIn("requirements-debug.txt", LanguageModelBackendNotInstalled.MESSAGE)
