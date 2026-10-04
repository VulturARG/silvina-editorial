from dataclasses import dataclass

from src.domain.dtos.base_dto import BaseDTO


@dataclass(frozen=True)
class FeedbackLineDTO(BaseDTO):
    """Represents a prepared feedback line with its indentation level."""

    text: str
    indentation: int
