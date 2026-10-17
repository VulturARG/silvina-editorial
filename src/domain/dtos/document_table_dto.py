from dataclasses import dataclass

from src.domain.dtos.base_dto import BaseDTO


@dataclass(frozen=True)
class DocumentTableDTO(BaseDTO):
    """Rows of cell texts of a table, with the number of non-empty paragraphs that precede it."""

    rows: tuple[tuple[str, ...], ...]
    position: int
