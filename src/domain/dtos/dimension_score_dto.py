from dataclasses import dataclass

from src.domain.dtos.base_dto import BaseDTO
from src.domain.dtos.feedback_block_dto import FeedbackBlockDTO


@dataclass(frozen=True)
class DimensionScoreDTO(BaseDTO):
    """A single dimension's parsed score and feedback text."""

    score: float
    feedback: str
    feedback_blocks: tuple[FeedbackBlockDTO, ...] = ()
