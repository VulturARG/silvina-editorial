from dataclasses import FrozenInstanceError
from typing import Any
from unittest import TestCase

from src.domain.dtos.classification_text_sampling_settings_dto import (
    ClassificationTextSamplingSettingsDTO,
)


class TestClassificationTextSamplingSettingsDTO(TestCase):
    def _make_dto(self) -> ClassificationTextSamplingSettingsDTO:
        return ClassificationTextSamplingSettingsDTO(
            introduction_character_limit=3500,
            conclusion_character_limit=2500,
            fallback_character_limit=6000,
            bibliography_header_max_length=30,
        )

    def test_requires_all_fields_raising_type_error_when_missing(self):
        kwargs: dict[str, Any] = {}
        with self.assertRaises(TypeError):
            ClassificationTextSamplingSettingsDTO(**kwargs)

    def test_constructs_with_provided_values(self):
        dto = self._make_dto()
        self.assertEqual(dto.introduction_character_limit, 3500)
        self.assertEqual(dto.conclusion_character_limit, 2500)
        self.assertEqual(dto.fallback_character_limit, 6000)
        self.assertEqual(dto.bibliography_header_max_length, 30)

    def test_is_immutable_raising_frozen_instance_error_on_mutation(self):
        dto = self._make_dto()
        field_name = "introduction_character_limit"
        with self.assertRaises(FrozenInstanceError):
            setattr(dto, field_name, 4000)

    def test_as_dict_returns_plain_dictionary(self):
        dto = self._make_dto()
        expected = {
            "introduction_character_limit": 3500,
            "conclusion_character_limit": 2500,
            "fallback_character_limit": 6000,
            "bibliography_header_max_length": 30,
        }
        self.assertEqual(dto.as_dict(), expected)

    def test_from_dict_reconstructs_equal_instance(self):
        dto = self._make_dto()
        reconstructed = ClassificationTextSamplingSettingsDTO.from_dict(dto.as_dict())
        self.assertEqual(reconstructed, dto)
