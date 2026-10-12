from dataclasses import dataclass

from src.domain.dtos.base_dto import BaseDTO


@dataclass(frozen=True)
class CaptionNormsDTO(BaseDTO):
    """Editorial norms for caption prefixes in figures or tables."""

    caption_prefixes: tuple[str, ...]
