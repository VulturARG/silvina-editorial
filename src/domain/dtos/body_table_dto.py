from dataclasses import dataclass

from src.domain.dtos.base_dto import BaseDTO


@dataclass(frozen=True)
class BodyTableDTO(BaseDTO):
    """Markdown rendering of a document table and the number of paragraphs that precede it."""

    markdown: str
    position: int
