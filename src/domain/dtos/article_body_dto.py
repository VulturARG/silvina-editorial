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
        """Return the text with each table's Markdown at its position, set apart by blank lines."""
        if not self.tables:
            return self.text
        text = self.title
        previous_is_table = False
        for block, is_table in self._blocks_in_document_order():
            separator = "\n\n" if is_table or previous_is_table else " "
            text += separator + block
            previous_is_table = is_table
        return text

    def _blocks_in_document_order(self) -> list[tuple[str, bool]]:
        blocks: list[tuple[str, bool]] = []
        for position in range(len(self.paragraphs) + 1):
            blocks.extend(
                (table.markdown, True) for table in self.tables if table.position == position
            )
            if position < len(self.paragraphs):
                blocks.append((self.paragraphs[position], False))
        return blocks

    @property
    def char_count(self) -> int:
        """Return the length of the title and body paragraphs joined with a single space."""
        return len(self.text)
