from src.domain.dtos.grammar_error_dto import GrammarErrorDTO
from src.domain.grammar.grammar_check_port import GrammarCheckPort


class RecordingGrammarCheckPort(GrammarCheckPort):
    """Test double for GrammarCheckPort that records the paragraphs of the last check call."""

    def __init__(self) -> None:
        self.received_paragraphs: list[str] | None = None

    def check(self, paragraphs: list[str]) -> list[GrammarErrorDTO]:
        """Record the received paragraphs and report no grammar errors."""
        self.received_paragraphs = list(paragraphs)
        return []
