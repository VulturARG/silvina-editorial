from dataclasses import dataclass

from src.domain.dtos.base_dto import BaseDTO


@dataclass(frozen=True)
class GrammarErrorDTO(BaseDTO):
    """A single grammar error found in the text.

    The offset and the length are counted in characters over the text sent to the grammar
    check: the abstract paragraphs, the repeated title and the body paragraphs joined with a
    newline. They are not positions in the article body alone.
    """

    number: int
    message: str
    context: str
    offset: int
    length: int
    replacements: list[str]
