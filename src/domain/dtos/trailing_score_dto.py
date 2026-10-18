from dataclasses import dataclass

from src.domain.dtos.base_dto import BaseDTO


@dataclass(frozen=True)
class TrailingScoreDTO(BaseDTO):
    """A score written on the last line of a dimension block and the block without that line."""

    score: float
    block_without_score_line: str
