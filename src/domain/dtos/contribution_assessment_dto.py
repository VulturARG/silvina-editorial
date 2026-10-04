from dataclasses import dataclass

from src.domain.dtos.base_dto import BaseDTO
from src.domain.enums.contribution_verdict import ContributionVerdict


@dataclass(frozen=True)
class ContributionAssessmentDTO(BaseDTO):
    """Immutable parsed assessment of editorial contribution."""

    verdict: ContributionVerdict
    phrase: str
    observation: str
