from src.domain.enums.contribution_verdict import ContributionVerdict
from src.domain.quality.suitability_field_truncator import SuitabilityFieldTruncator

_NOT_SUSTAINED_OBSERVATION = "Sin contribución observada o declarada."
_PARTIAL_OBSERVATION = "Contribución declarada pero no suficientemente sustentada."
_SUSTAINED_OBSERVATION_FALLBACK = "Contribución sustentada."


class ContributionObservationBuilder:
    """Builds standardized Spanish observation messages for contribution assessments."""

    def __init__(
        self,
        field_truncator: SuitabilityFieldTruncator,
        max_length: int,
    ) -> None:
        self._field_truncator = field_truncator
        self._max_length = max_length

    def build_observation(self, verdict: ContributionVerdict, phrase: str) -> str:
        """Build observation string based on verdict and phrase with truncation."""
        if verdict == ContributionVerdict.NOT_SUPPORTED:
            return _NOT_SUSTAINED_OBSERVATION
        if verdict == ContributionVerdict.PARTIAL:
            return _PARTIAL_OBSERVATION
        if not phrase:
            return _SUSTAINED_OBSERVATION_FALLBACK
        return self._field_truncator.truncate(
            f"Contribución sustentada — {phrase}", self._max_length
        )
