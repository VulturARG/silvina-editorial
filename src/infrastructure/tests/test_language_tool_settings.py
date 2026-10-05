from dataclasses import FrozenInstanceError
from typing import Any
from unittest import TestCase

from src.infrastructure.adapters.grammar.language_tool_settings import (
    LanguageToolSettings,
)


class TestLanguageToolSettings(TestCase):
    def _make_settings(self) -> LanguageToolSettings:
        return LanguageToolSettings(
            max_replacements=3,
            max_paragraphs=20,
            max_chars=5000,
            max_errors=10,
        )

    def test_requires_all_fields_raising_type_error_when_missing(self):
        kwargs: dict[str, Any] = {}
        with self.assertRaises(TypeError):
            LanguageToolSettings(**kwargs)

    def test_constructs_with_provided_values(self):
        settings = self._make_settings()
        self.assertEqual(settings.max_replacements, 3)
        self.assertEqual(settings.max_paragraphs, 20)
        self.assertEqual(settings.max_chars, 5000)
        self.assertEqual(settings.max_errors, 10)

    def test_is_immutable_raising_frozen_instance_error_on_mutation(self):
        settings = self._make_settings()
        field_name = "max_replacements"
        with self.assertRaises(FrozenInstanceError):
            setattr(settings, field_name, 5)
