from dataclasses import dataclass

from src.domain.dtos.base_dto import BaseDTO
from src.domain.dtos.feedback_line_dto import FeedbackLineDTO
from src.domain.enums.feedback_line_kind import FeedbackLineKind


@dataclass(frozen=True)
class ClassifiedFeedbackLineDTO(BaseDTO):
    """Represents a classified feedback line along with its extracted structural payload."""

    kind: FeedbackLineKind
    line: FeedbackLineDTO
    title_text: str = ""
    heading_level: int = 0
    list_marker: str = ""
    item_content: str = ""
    starts_unindented_children: bool = False
