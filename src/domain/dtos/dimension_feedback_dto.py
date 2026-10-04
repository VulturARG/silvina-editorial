from dataclasses import dataclass

from src.domain.dtos.base_dto import BaseDTO
from src.domain.dtos.feedback_block_dto import FeedbackBlockDTO


@dataclass(frozen=True)
class DimensionFeedbackDTO(BaseDTO):
    """Immutable parsed feedback text and structured blocks for a dimension."""

    feedback: str
    blocks: tuple[FeedbackBlockDTO, ...] = ()
