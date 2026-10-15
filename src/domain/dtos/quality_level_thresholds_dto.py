from dataclasses import dataclass

from src.domain.dtos.base_dto import BaseDTO


@dataclass(frozen=True)
class QualityLevelThresholdsDTO(BaseDTO):
    """Minimum overall scores required to reach each quality level, from highest to lowest."""

    excellent_threshold: float
    good_threshold: float
    acceptable_threshold: float
    needs_improvement_threshold: float
