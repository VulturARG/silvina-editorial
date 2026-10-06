from dataclasses import dataclass

from src.domain.dtos.base_dto import BaseDTO
from src.domain.enums.alignment_verdict import AlignmentVerdict


@dataclass(frozen=True)
class AlignmentAssessmentDTO(BaseDTO):
    """Immutable parsed assessment of editorial alignment."""

    verdict: AlignmentVerdict
    lines: str
    justification: str
