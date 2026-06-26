from abc import ABC, abstractmethod

from src.domain.dtos.character_count_dto import CharacterCountDTO


class CharacterCountPort(ABC):
    """Port for obtaining accurate character and word counts from a document."""

    @abstractmethod
    def count(self, docx_path: str) -> CharacterCountDTO | None:
        """Return accurate counts for the document at the given path, or None if unavailable."""
