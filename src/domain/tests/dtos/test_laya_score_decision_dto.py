from dataclasses import FrozenInstanceError
from unittest import TestCase

from src.domain.dtos.base_dto import BaseDTO
from src.domain.dtos.laya_score_decision_dto import LayaScoreDecisionDTO


class TestLayaScoreDecisionDTO(TestCase):
    def test_is_frozen_dataclass_extending_base_dto(self):
        self.assertTrue(issubclass(LayaScoreDecisionDTO, BaseDTO))
        score = LayaScoreDecisionDTO(expected_value=7.5, confidence=0.6)
        with self.assertRaises(FrozenInstanceError):
            score.expected_value = 5.0

    def test_holds_expected_value_and_confidence(self):
        score = LayaScoreDecisionDTO(expected_value=7.5, confidence=0.6)
        self.assertEqual(score.expected_value, 7.5)
        self.assertEqual(score.confidence, 0.6)
