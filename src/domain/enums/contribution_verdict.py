from enum import Enum


class ContributionVerdict(Enum):
    """Contribution evaluation verdicts ordered from most specific to least specific.

    Declaration order is significant: matching evaluates candidates in declaration
    order because more specific strings contain less specific ones, and the first
    member serves as the fallback default when no candidate matches.
    """

    NOT_SUPPORTED = "NO SUSTENTADA"
    PARTIAL = "PARCIAL"
    SUPPORTED = "SUSTENTADA"
