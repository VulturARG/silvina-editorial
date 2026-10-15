from dataclasses import dataclass

from src.domain.dtos.base_dto import BaseDTO


@dataclass(frozen=True)
class ArticleLengthNormsDTO(BaseDTO):
    """Editorial norms for the maximum size of an article body."""

    max_body_chars: int
