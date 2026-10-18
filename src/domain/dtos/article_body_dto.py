from dataclasses import dataclass

from src.domain.dtos.base_dto import BaseDTO
from src.domain.dtos.body_table_dto import BodyTableDTO


@dataclass(frozen=True)
class ArticleBodyDTO(BaseDTO):
    """Title, abstract paragraphs and body paragraphs located in a document."""

    title: str
    abstract_paragraphs: tuple[str, ...]
    paragraphs: tuple[str, ...]
    tables: tuple[BodyTableDTO, ...] = ()

    @property
    def abstract_and_body_paragraphs(self) -> list[str]:
        """Return the abstract paragraphs, the repeated title and the body paragraphs in order."""
        return [*self.abstract_paragraphs, self.title, *self.paragraphs]

    @property
    def text(self) -> str:
        """Return the title and body paragraphs joined with a single space."""
        return " ".join((self.title, *self.paragraphs))

    @property
    def text_with_tables(self) -> str:
        """Return the title and body blocks in document order, each separated by a blank line."""
        return "\n\n".join((self.title, *self._blocks_in_document_order()))

    @property
    def paragraphs_text_with_tables(self) -> str:
        """Return the body paragraphs and table Markdown in document order, separated by blank lines."""
        return "\n\n".join(self._blocks_in_document_order())

    def _blocks_in_document_order(self) -> list[str]:
        blocks: list[str] = []
        for position in range(len(self.paragraphs) + 1):
            blocks.extend(table.markdown for table in self.tables if table.position == position)
            if position < len(self.paragraphs):
                blocks.append(self.paragraphs[position])
        return blocks

    @property
    def char_count(self) -> int:
        """Return the length of the title and body paragraphs joined with a single space."""
        return len(self.text)
