from enum import Enum


class EditorialAlignmentVerdict(Enum):
    """Alignment verdict categories for editorial suitability evaluation."""

    ALIGNED = "ALINEADO"
    PARTIALLY_ALIGNED = "PARCIALMENTE ALINEADO"
    NOT_ALIGNED = "NO ALINEADO"
