from enum import Enum
from typing import TypeVar

VerdictEnum = TypeVar("VerdictEnum", bound=Enum)


class SuitabilityVerdictMatcher:
    """Matches raw verdict text against domain verdict enums."""

    def match(
        self,
        raw_verdict_text: str,
        verdict_type: type[VerdictEnum],
    ) -> VerdictEnum:
        """Match verdict text against enum values in declaration order with fallback to first member."""
        for candidate in verdict_type:
            if candidate.value in raw_verdict_text:
                return candidate
        return next(iter(verdict_type))
