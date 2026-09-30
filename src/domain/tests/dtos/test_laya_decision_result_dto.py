from dataclasses import FrozenInstanceError
from unittest import TestCase

from src.domain.dtos.base_dto import BaseDTO
from src.domain.dtos.laya_choice_decision_dto import LayaChoiceDecisionDTO
from src.domain.dtos.laya_decision_result_dto import LayaDecisionResultDTO
from src.domain.dtos.laya_score_decision_dto import LayaScoreDecisionDTO


def build_choice(answer: str, probabilities: dict[str, float]) -> LayaChoiceDecisionDTO:
    return LayaChoiceDecisionDTO(
        answer=answer, probabilities=probabilities, confidence=probabilities[answer]
    )


def build_decision_result() -> LayaDecisionResultDTO:
    return LayaDecisionResultDTO(
        s4_research_intent=build_choice("SI", {"SI": 0.9, "NO": 0.1}),
        s5_empirical_evidence=build_choice("NO", {"SI": 0.3, "NO": 0.7}),
        s6_theoretical_framework=build_choice("SI", {"SI": 0.8, "NO": 0.2}),
        editorial_verdict=build_choice(
            "PARCIAL", {"SUSTENTADA": 0.2, "PARCIAL": 0.6, "NO SUSTENTADA": 0.2}
        ),
        research_line=build_choice("4", {"4": 0.75, "NINGUNA": 0.25}),
        score_clarity=LayaScoreDecisionDTO(expected_value=7.5, confidence=0.6),
        score_coherence=LayaScoreDecisionDTO(expected_value=6.2, confidence=0.5),
        score_argumentation=LayaScoreDecisionDTO(expected_value=5.0, confidence=0.4),
        score_conclusions=LayaScoreDecisionDTO(expected_value=8.1, confidence=0.7),
    )


class TestLayaDecisionResultDTO(TestCase):
    def test_is_frozen_dataclass_extending_base_dto(self):
        self.assertTrue(issubclass(LayaDecisionResultDTO, BaseDTO))
        decision_result = build_decision_result()
        with self.assertRaises(FrozenInstanceError):
            decision_result.s4_research_intent = build_choice("NO", {"SI": 0.1, "NO": 0.9})

    def test_holds_choice_decisions(self):
        decision_result = build_decision_result()
        self.assertEqual(decision_result.s4_research_intent.answer, "SI")
        self.assertEqual(decision_result.s5_empirical_evidence.answer, "NO")
        self.assertEqual(decision_result.s6_theoretical_framework.answer, "SI")
        self.assertEqual(decision_result.editorial_verdict.answer, "PARCIAL")
        self.assertEqual(decision_result.research_line.answer, "4")

    def test_holds_score_decisions(self):
        decision_result = build_decision_result()
        self.assertEqual(decision_result.score_clarity.expected_value, 7.5)
        self.assertEqual(decision_result.score_coherence.expected_value, 6.2)
        self.assertEqual(decision_result.score_argumentation.expected_value, 5.0)
        self.assertEqual(decision_result.score_conclusions.expected_value, 8.1)

    def test_round_trips_through_dict_rebuilding_nested_decisions(self):
        decision_result = build_decision_result()
        rebuilt = LayaDecisionResultDTO.from_dict(decision_result.as_dict())
        self.assertEqual(rebuilt, decision_result)
        self.assertIsInstance(rebuilt.s4_research_intent, LayaChoiceDecisionDTO)
        self.assertIsInstance(rebuilt.score_clarity, LayaScoreDecisionDTO)
