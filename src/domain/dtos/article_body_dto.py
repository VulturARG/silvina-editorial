from dataclasses import dataclass

from src.domain.dtos.base_dto import BaseDTO


@dataclass(frozen=True)
class ArticleBodyDTO(BaseDTO):
    """Title, abstract paragraphs and body paragraphs located in a document."""

    title: str
    abstract_paragraphs: tuple[str, ...]
    paragraphs: tuple[str, ...]
