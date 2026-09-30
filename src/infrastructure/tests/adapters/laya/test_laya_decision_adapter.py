from json import loads
from typing import Any
from unittest import TestCase

from src.domain.dtos.laya_choice_decision_dto import LayaChoiceDecisionDTO
from src.domain.dtos.laya_score_decision_dto import LayaScoreDecisionDTO
from src.domain.laya.laya_decision_port import LayaDecisionPort
from src.infrastructure.adapters.laya.laya_decision_adapter import LayaDecisionAdapter
from src.infrastructure.resources.laya import LAYA_RESOURCES_DIR
from src.infrastructure.resources.text_resource_loader import read_text_resource
from src.infrastructure.tests.test_doubles.fake_laya_agent import FakeLayaAgent


def build_choice_answer(choice: str, probabilities: dict[str, float]) -> dict[str, Any]:
    return {
        "type": "choice",
        "choice": choice,
        "probabilities": probabilities,
        "confidence": 0.5,
        "answer_confidence": probabilities[choice],
    }


def build_score_answer(score: float, answer_confidence: float) -> dict[str, Any]:
    return {
        "type": "score",
        "score": score,
        "probabilities": {},
        "confidence": 0.5,
        "answer_confidence": answer_confidence,
    }


def build_answers() -> dict[str, dict[str, Any]]:
    return {
        "s4_intent": build_choice_answer("SI", {"SI": 0.9, "NO": 0.1}),
        "s5_evidence": build_choice_answer("NO", {"SI": 0.3, "NO": 0.7}),
        "s6_theory": build_choice_answer("SI", {"SI": 0.8, "NO": 0.2}),
        "editorial_verdict": build_choice_answer(
            "PARCIAL", {"SUSTENTADA": 0.2, "PARCIAL": 0.6, "NO SUSTENTADA": 0.2}
        ),
        "research_line": build_choice_answer("4", {"4": 0.75, "NINGUNA": 0.25}),
        "score_clarity": build_score_answer(7.5, 0.6),
        "score_coherence": build_score_answer(6.2, 0.5),
        "score_argumentation": build_score_answer(5.0, 0.4),
        "score_conclusions": build_score_answer(8.1, 0.7),
    }


def load_decision_questions() -> dict[str, dict[str, Any]]:
    return loads(
        read_text_resource(directory=LAYA_RESOURCES_DIR, filename="decision_questions.json")
    )


class TestLayaDecisionAdapter(TestCase):
    def test_is_subclass_of_laya_decision_port(self):
        self.assertTrue(issubclass(LayaDecisionAdapter, LayaDecisionPort))

    def test_decide_sends_text_sample_as_state_with_configured_questions(self):
        questions = load_decision_questions()
        agent = FakeLayaAgent(answers=build_answers())
        adapter = LayaDecisionAdapter(agent=agent, questions=questions)

        adapter.decide(text_sample="Texto del articulo")

        self.assertEqual(agent.received_states, ["Texto del articulo"])
        self.assertEqual(agent.received_questions, [questions])

    def test_decide_maps_question_ids_to_choice_decisions(self):
        adapter = LayaDecisionAdapter(
            agent=FakeLayaAgent(answers=build_answers()), questions=load_decision_questions()
        )

        result = adapter.decide(text_sample="Texto")

        self.assertEqual(
            result.s4_research_intent,
            LayaChoiceDecisionDTO(
                answer="SI", probabilities={"SI": 0.9, "NO": 0.1}, confidence=0.9
            ),
        )
        self.assertEqual(result.s5_empirical_evidence.answer, "NO")
        self.assertEqual(result.s6_theoretical_framework.answer, "SI")
        self.assertEqual(result.editorial_verdict.answer, "PARCIAL")
        self.assertEqual(result.editorial_verdict.confidence, 0.6)
        self.assertEqual(result.research_line.answer, "4")

    def test_decide_maps_question_ids_to_score_decisions(self):
        adapter = LayaDecisionAdapter(
            agent=FakeLayaAgent(answers=build_answers()), questions=load_decision_questions()
        )

        result = adapter.decide(text_sample="Texto")

        self.assertEqual(
            result.score_clarity, LayaScoreDecisionDTO(expected_value=7.5, confidence=0.6)
        )
        self.assertEqual(result.score_coherence.expected_value, 6.2)
        self.assertEqual(result.score_argumentation.expected_value, 5.0)
        self.assertEqual(result.score_conclusions.expected_value, 8.1)

    def test_decide_raises_key_error_when_an_answer_is_missing(self):
        answers = build_answers()
        del answers["research_line"]
        adapter = LayaDecisionAdapter(
            agent=FakeLayaAgent(answers=answers), questions=load_decision_questions()
        )

        with self.assertRaises(KeyError):
            adapter.decide(text_sample="Texto")

    def test_decision_questions_resource_defines_the_nine_mapped_questions(self):
        self.assertEqual(
            set(load_decision_questions()),
            {
                "s4_intent",
                "s5_evidence",
                "s6_theory",
                "editorial_verdict",
                "research_line",
                "score_clarity",
                "score_coherence",
                "score_argumentation",
                "score_conclusions",
            },
        )
