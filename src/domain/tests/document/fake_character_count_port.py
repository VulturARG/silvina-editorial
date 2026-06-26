from src.domain.document.character_count_port import CharacterCountPort
from src.domain.dtos.character_count_dto import CharacterCountDTO


class FakeCharacterCountPort(CharacterCountPort):
    """Test double for CharacterCountPort with configurable CharacterCountDTO or None return."""

    def __init__(self, result: CharacterCountDTO | None = None) -> None:
        self._result = result

    def count(self, docx_path: str) -> CharacterCountDTO | None:
        """Return the configured result (None by default, simulating unavailability)."""
        return self._result
