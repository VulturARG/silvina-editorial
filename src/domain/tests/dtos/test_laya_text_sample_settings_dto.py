from dataclasses import FrozenInstanceError
from unittest import TestCase

from src.domain.dtos.base_dto import BaseDTO
from src.domain.dtos.laya_text_sample_settings_dto import LayaTextSampleSettingsDTO


def build_settings() -> LayaTextSampleSettingsDTO:
    return LayaTextSampleSettingsDTO(
        min_sample_word_count=400,
        text_sample_character_limit=8000,
        reference_line_prefix_length=80,
        introduction_paragraph_count=3,
        middle_paragraph_count=2,
        conclusion_paragraph_limit=3,
        fallback_tail_paragraph_count=2,
        conclusion_header_marker="conclusi",
    )


class TestLayaTextSampleSettingsDTO(TestCase):
    def test_is_frozen_dataclass_extending_base_dto(self):
        self.assertTrue(issubclass(LayaTextSampleSettingsDTO, BaseDTO))
        settings = build_settings()
        with self.assertRaises(FrozenInstanceError):
            settings.text_sample_character_limit = 100

    def test_holds_all_sampling_settings(self):
        settings = build_settings()
        self.assertEqual(settings.min_sample_word_count, 400)
        self.assertEqual(settings.text_sample_character_limit, 8000)
        self.assertEqual(settings.reference_line_prefix_length, 80)
        self.assertEqual(settings.introduction_paragraph_count, 3)
        self.assertEqual(settings.middle_paragraph_count, 2)
        self.assertEqual(settings.conclusion_paragraph_limit, 3)
        self.assertEqual(settings.fallback_tail_paragraph_count, 2)
        self.assertEqual(settings.conclusion_header_marker, "conclusi")
