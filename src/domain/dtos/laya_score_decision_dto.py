from dataclasses import dataclass

from src.domain.dtos.base_dto import BaseDTO


@dataclass(frozen=True)
class LayaScoreDecisionDTO(BaseDTO):
    """A Laya score answer as its 0-10 expected value and answer confidence."""

    expected_value: float
    confidence: float
