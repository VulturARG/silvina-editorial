from dataclasses import dataclass

from src.domain.dtos.base_dto import BaseDTO
from src.domain.enums.feedback_block_kind import FeedbackBlockKind


@dataclass(frozen=True)
class FeedbackBlockDTO(BaseDTO):
    """Represents a structured block within dimension feedback."""

    kind: FeedbackBlockKind
    text: str
    level: int = 0
    marker: str = ""
