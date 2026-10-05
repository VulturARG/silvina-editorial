from dataclasses import FrozenInstanceError
from typing import Any
from unittest import TestCase

from src.domain.dtos.quality_text_sampling_settings_dto import (
    QualityTextSamplingSettingsDTO,
)


class TestQualityTextSamplingSettingsDTO(TestCase):
    def _make_dto(self) -> QualityTextSamplingSettingsDTO:
        return QualityTextSamplingSettingsDTO(
            min_sample_word_count=400,
            text_sample_character_limit=8000,
            reference_line_prefix_length=80,
            introduction_paragraph_count=3,
            middle_paragraph_count=2,
            conclusion_paragraph_limit=3,
            fallback_tail_paragraph_count=2,
            conclusion_header_marker="conclusi",
        )

    def test_requires_all_fields_raising_type_error_when_missing(self):
        kwargs: dict[str, Any] = {}
        with self.assertRaises(TypeError):
            QualityTextSamplingSettingsDTO(**kwargs)

    def test_constructs_with_provided_values(self):
        dto = self._make_dto()
        self.assertEqual(dto.min_sample_word_count, 400)
        self.assertEqual(dto.text_sample_character_limit, 8000)
        self.assertEqual(dto.reference_line_prefix_length, 80)
        self.assertEqual(dto.introduction_paragraph_count, 3)
        self.assertEqual(dto.middle_paragraph_count, 2)
        self.assertEqual(dto.conclusion_paragraph_limit, 3)
        self.assertEqual(dto.fallback_tail_paragraph_count, 2)
        self.assertEqual(dto.conclusion_header_marker, "conclusi")

    def test_is_immutable_raising_frozen_instance_error_on_mutation(self):
        dto = self._make_dto()
        field_name = "min_sample_word_count"
        with self.assertRaises(FrozenInstanceError):
            setattr(dto, field_name, 500)

    def test_as_dict_returns_plain_dictionary(self):
        dto = self._make_dto()
        expected = {
            "min_sample_word_count": 400,
            "text_sample_character_limit": 8000,
            "reference_line_prefix_length": 80,
            "introduction_paragraph_count": 3,
            "middle_paragraph_count": 2,
            "conclusion_paragraph_limit": 3,
            "fallback_tail_paragraph_count": 2,
            "conclusion_header_marker": "conclusi",
        }
        self.assertEqual(dto.as_dict(), expected)

    def test_from_dict_reconstructs_equal_instance(self):
        dto = self._make_dto()
        reconstructed = QualityTextSamplingSettingsDTO.from_dict(dto.as_dict())
        self.assertEqual(reconstructed, dto)
