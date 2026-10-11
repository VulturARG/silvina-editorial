from dataclasses import dataclass
from typing import Self

from src.domain.enums.feedback_block_kind import FeedbackBlockKind
from src.infrastructure.adapters.report.docx_feedback_block_payload import (
    DocxFeedbackBlockPayload,
)

_FEEDBACK_BLOCK_KINDS_BY_VALUE = {kind.value: kind for kind in FeedbackBlockKind}


@dataclass(frozen=True)
class DocxFeedbackBlockView:
    """Normalized view of a feedback block for Word report rendering."""

    kind: FeedbackBlockKind
    text: str
    level: int
    marker: str

    @classmethod
    def from_payload(cls, payload: DocxFeedbackBlockPayload) -> Self:
        """Build a view from a serialized block, treating unknown kinds as text."""
        return cls(
            kind=_FEEDBACK_BLOCK_KINDS_BY_VALUE.get(
                payload.get("kind", ""),
                FeedbackBlockKind.TEXT,
            ),
            text=payload.get("text", ""),
            level=payload.get("level", 0),
            marker=payload.get("marker", ""),
        )
