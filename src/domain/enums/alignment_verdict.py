from enum import Enum


class AlignmentVerdict(Enum):
    """Alignment evaluation verdicts ordered from most specific to least specific.

    Declaration order is significant: matching evaluates candidates in declaration
    order because more specific strings contain less specific ones, and the first
    member serves as the fallback default when no candidate matches.
    """

    NOT_ALIGNED = "NO ALINEADO"
    PARTIALLY_ALIGNED = "PARCIALMENTE ALINEADO"
    ALIGNED = "ALINEADO"
