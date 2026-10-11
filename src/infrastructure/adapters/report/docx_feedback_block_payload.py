from typing import TypedDict


class DocxFeedbackBlockPayload(TypedDict, total=False):
    """Serialized feedback block as stored in quality dimension scores."""

    kind: str
    text: str
    level: int
    marker: str
