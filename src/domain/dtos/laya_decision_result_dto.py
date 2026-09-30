from dataclasses import dataclass
from typing import Any

from src.domain.dtos.base_dto import BaseDTO
from src.domain.dtos.laya_choice_decision_dto import LayaChoiceDecisionDTO
from src.domain.dtos.laya_score_decision_dto import LayaScoreDecisionDTO


@dataclass(frozen=True)
class LayaDecisionResultDTO(BaseDTO):
    """The 9 raw Laya decisions for a document."""

    s4_research_intent: LayaChoiceDecisionDTO
    s5_empirical_evidence: LayaChoiceDecisionDTO
    s6_theoretical_framework: LayaChoiceDecisionDTO
    editorial_verdict: LayaChoiceDecisionDTO
    research_line: LayaChoiceDecisionDTO
    score_clarity: LayaScoreDecisionDTO
    score_coherence: LayaScoreDecisionDTO
    score_argumentation: LayaScoreDecisionDTO
    score_conclusions: LayaScoreDecisionDTO

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LayaDecisionResultDTO":
        """Creates an instance rebuilding each nested choice and score decision."""
        return cls(
            s4_research_intent=LayaChoiceDecisionDTO.from_dict(data["s4_research_intent"]),
            s5_empirical_evidence=LayaChoiceDecisionDTO.from_dict(data["s5_empirical_evidence"]),
            s6_theoretical_framework=LayaChoiceDecisionDTO.from_dict(
                data["s6_theoretical_framework"]
            ),
            editorial_verdict=LayaChoiceDecisionDTO.from_dict(data["editorial_verdict"]),
            research_line=LayaChoiceDecisionDTO.from_dict(data["research_line"]),
            score_clarity=LayaScoreDecisionDTO.from_dict(data["score_clarity"]),
            score_coherence=LayaScoreDecisionDTO.from_dict(data["score_coherence"]),
            score_argumentation=LayaScoreDecisionDTO.from_dict(data["score_argumentation"]),
            score_conclusions=LayaScoreDecisionDTO.from_dict(data["score_conclusions"]),
        )
