from src.domain.dtos.laya_choice_decision_dto import LayaChoiceDecisionDTO
from src.domain.dtos.laya_decision_result_dto import LayaDecisionResultDTO
from src.domain.dtos.laya_score_decision_dto import LayaScoreDecisionDTO
from src.domain.laya.laya_decision_port import LayaDecisionPort


def _certain_choice(answer: str) -> LayaChoiceDecisionDTO:
    return LayaChoiceDecisionDTO(answer=answer, probabilities={answer: 1.0}, confidence=1.0)


_ZERO_SCORE = LayaScoreDecisionDTO(expected_value=0.0, confidence=1.0)

DEFAULT_DECISION_RESULT = LayaDecisionResultDTO(
    s4_research_intent=_certain_choice("NO"),
    s5_empirical_evidence=_certain_choice("NO"),
    s6_theoretical_framework=_certain_choice("NO"),
    editorial_verdict=_certain_choice("NO SUSTENTADA"),
    research_line=_certain_choice("NINGUNA"),
    score_clarity=_ZERO_SCORE,
    score_coherence=_ZERO_SCORE,
    score_argumentation=_ZERO_SCORE,
    score_conclusions=_ZERO_SCORE,
)


class FakeLayaDecisionPort(LayaDecisionPort):
    """Test double returning a configured decision result or raising a configured error."""

    def __init__(
        self,
        result: LayaDecisionResultDTO = DEFAULT_DECISION_RESULT,
        error: Exception | None = None,
    ) -> None:
        self._result = result
        self._error = error
        self.received_text_samples: list[str] = []

    def decide(self, text_sample: str) -> LayaDecisionResultDTO:
        self.received_text_samples.append(text_sample)
        if self._error is not None:
            raise self._error
        return self._result
