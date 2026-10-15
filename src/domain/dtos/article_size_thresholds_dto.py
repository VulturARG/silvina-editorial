from dataclasses import dataclass

from src.domain.dtos.base_dto import BaseDTO


@dataclass(frozen=True)
class ArticleSizeThresholdsDTO(BaseDTO):
    """Character-count boundaries used to classify an article's size."""

    short_min_chars: int
    short_max_chars: int
    undefined_min_chars: int
    undefined_max_chars: int
    long_min_chars: int
    long_max_chars: int
    extra_long_max_chars: int
