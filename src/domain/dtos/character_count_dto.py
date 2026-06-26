from dataclasses import dataclass

from src.domain.dtos.base_dto import BaseDTO


@dataclass(frozen=True)
class CharacterCountDTO(BaseDTO):
    """Accurate word, character, and paragraph counts obtained from a document source."""

    word_count: int
    char_count: int
    paragraph_count: int
