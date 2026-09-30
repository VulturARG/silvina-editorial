from dataclasses import FrozenInstanceError
from unittest import TestCase

from src.domain.dtos.base_dto import BaseDTO
from src.domain.dtos.laya_choice_decision_dto import LayaChoiceDecisionDTO


class TestLayaChoiceDecisionDTO(TestCase):
    def test_is_frozen_dataclass_extending_base_dto(self):
        self.assertTrue(issubclass(LayaChoiceDecisionDTO, BaseDTO))
        choice = LayaChoiceDecisionDTO(
            answer="SI", probabilities={"SI": 0.9, "NO": 0.1}, confidence=0.9
        )
        with self.assertRaises(FrozenInstanceError):
            choice.answer = "NO"

    def test_holds_answer_probabilities_and_confidence(self):
        choice = LayaChoiceDecisionDTO(
            answer="SI", probabilities={"SI": 0.9, "NO": 0.1}, confidence=0.9
        )
        self.assertEqual(choice.answer, "SI")
        self.assertEqual(choice.probabilities, {"SI": 0.9, "NO": 0.1})
        self.assertEqual(choice.confidence, 0.9)
