from typing import Any

from laya.agent import Agent

from src.domain.dtos.laya_choice_decision_dto import LayaChoiceDecisionDTO
from src.domain.dtos.laya_decision_result_dto import LayaDecisionResultDTO
from src.domain.dtos.laya_score_decision_dto import LayaScoreDecisionDTO
from src.domain.laya.laya_decision_port import LayaDecisionPort


class LayaDecisionAdapter(LayaDecisionPort):
    """Obtains all editorial decisions from a fine-tuned Laya agent in a single prediction."""

    def __init__(self, agent: Agent, questions: dict[str, dict[str, Any]]) -> None:
        self._agent = agent
        self._questions = questions

    def decide(self, text_sample: str) -> LayaDecisionResultDTO:
        """Predict every configured question for the text sample and map the answers."""
        answers = self._agent.predict(state=text_sample, questions=self._questions)["answers"]
        return LayaDecisionResultDTO(
            s4_research_intent=self._to_choice_decision(answers["s4_intent"]),
            s5_empirical_evidence=self._to_choice_decision(answers["s5_evidence"]),
            s6_theoretical_framework=self._to_choice_decision(answers["s6_theory"]),
            editorial_verdict=self._to_choice_decision(answers["editorial_verdict"]),
            research_line=self._to_choice_decision(answers["research_line"]),
            score_clarity=self._to_score_decision(answers["score_clarity"]),
            score_coherence=self._to_score_decision(answers["score_coherence"]),
            score_argumentation=self._to_score_decision(answers["score_argumentation"]),
            score_conclusions=self._to_score_decision(answers["score_conclusions"]),
        )

    def _to_choice_decision(self, answer: dict[str, Any]) -> LayaChoiceDecisionDTO:
        return LayaChoiceDecisionDTO(
            answer=answer["choice"],
            probabilities=answer["probabilities"],
            confidence=answer["answer_confidence"],
        )

    def _to_score_decision(self, answer: dict[str, Any]) -> LayaScoreDecisionDTO:
        return LayaScoreDecisionDTO(
            expected_value=answer["score"],
            confidence=answer["answer_confidence"],
        )
