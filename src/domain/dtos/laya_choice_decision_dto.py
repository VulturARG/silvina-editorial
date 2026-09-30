from dataclasses import dataclass

from src.domain.dtos.base_dto import BaseDTO


@dataclass(frozen=True)
class LayaChoiceDecisionDTO(BaseDTO):
    """A Laya choice answer with its per-option probabilities and answer confidence."""

    answer: str
    probabilities: dict[str, float]
    confidence: float
