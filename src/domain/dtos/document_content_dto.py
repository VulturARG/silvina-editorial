from dataclasses import dataclass, field

from src.domain.dtos.base_dto import BaseDTO
from src.domain.dtos.reference_dto import ReferenceDTO
from src.domain.enums.extraction_fallback import ExtractionFallback


@dataclass(frozen=True)
class DocumentContentDTO(BaseDTO):
    """Represents the extracted content of a document."""

    word_count: int
    char_count: int
    paragraph_count: int = 0
    title: str | None = None
    authors: str | None = None
    abstract: str | None = None
    keywords: list[str] = field(default_factory=list)
    references: list[ReferenceDTO] = field(default_factory=list)
    paragraphs: list[str] = field(default_factory=list)
    sections: dict[str, str] = field(default_factory=dict)

    @property
    def display_authors(self) -> str:
        """Return authors or a fallback string when authors is absent."""
        return self.authors or ExtractionFallback.UNKNOWN_AUTHOR
