from dataclasses import FrozenInstanceError
from unittest import TestCase

from src.domain.dtos.base_dto import BaseDTO
from src.domain.dtos.stage_duration_dto import StageDurationDTO


class TestStageDurationDTO(TestCase):
    def test_is_subclass_of_base_dto(self):
        self.assertTrue(issubclass(StageDurationDTO, BaseDTO))

    def test_frozen_raises_on_mutation(self):
        stage_duration = StageDurationDTO(
            analysis_id="analysis-123",
            stage_name="content_extraction",
            duration_ms=150.5,
        )
        field_name = "duration_ms"
        with self.assertRaises(FrozenInstanceError):
            setattr(stage_duration, field_name, 200.0)

    def test_holds_expected_attributes(self):
        stage_duration = StageDurationDTO(
            analysis_id="analysis-123",
            stage_name="content_extraction",
            duration_ms=150.5,
        )
        self.assertEqual(stage_duration.analysis_id, "analysis-123")
        self.assertEqual(stage_duration.stage_name, "content_extraction")
        self.assertEqual(stage_duration.duration_ms, 150.5)
