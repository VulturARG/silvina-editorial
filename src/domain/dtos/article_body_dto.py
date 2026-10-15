from dataclasses import dataclass

from src.domain.dtos.base_dto import BaseDTO


@dataclass(frozen=True)
class ArticleBodyDTO(BaseDTO):
    """Title, abstract paragraphs and body paragraphs located in a document."""

    title: str
    abstract_paragraphs: tuple[str, ...]
    paragraphs: tuple[str, ...]

    @property
    def text(self) -> str:
        """Return the title and body paragraphs joined with a single space."""
        return " ".join((self.title, *self.paragraphs))

    @property
    def char_count(self) -> int:
        """Return the length of the title and body paragraphs joined with a single space."""
        return len(self.text)
