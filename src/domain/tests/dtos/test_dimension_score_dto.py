from dataclasses import FrozenInstanceError
from unittest import TestCase

from src.domain.dtos.base_dto import BaseDTO
from src.domain.dtos.dimension_score_dto import DimensionScoreDTO
from src.domain.dtos.feedback_block_dto import FeedbackBlockDTO
from src.domain.enums.feedback_block_kind import FeedbackBlockKind


class TestDimensionScoreDTO(TestCase):
    def test_is_frozen_dataclass_extending_base_dto(self):
        self.assertTrue(issubclass(DimensionScoreDTO, BaseDTO))
        dimension_score = DimensionScoreDTO(score=8.0, feedback="text")
        with self.assertRaises(FrozenInstanceError):
            dimension_score.score = 5.0  # type: ignore[misc]

    def test_holds_score_and_feedback_fields(self):
        dimension_score = DimensionScoreDTO(score=8.0, feedback="text")
        self.assertEqual(dimension_score.score, 8.0)
        self.assertEqual(dimension_score.feedback, "text")

    def test_feedback_blocks_defaults_to_empty_tuple(self):
        dimension_score = DimensionScoreDTO(score=8.0, feedback="text")
        self.assertEqual(dimension_score.feedback_blocks, ())

    def test_holds_explicit_feedback_blocks(self):
        block = FeedbackBlockDTO(kind=FeedbackBlockKind.ITEM, text="Detalle de retroalimentación")
        dimension_score = DimensionScoreDTO(
            score=8.0,
            feedback="Detalle de retroalimentación",
            feedback_blocks=(block,),
        )
        self.assertEqual(dimension_score.feedback_blocks, (block,))
