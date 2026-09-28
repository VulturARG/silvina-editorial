from src.domain.classification.research_intent_detector_port import (
    ResearchIntentDetectorPort,
)


class FakeResearchIntentDetectorPort(ResearchIntentDetectorPort):
    """Test double for ResearchIntentDetectorPort with configurable signals or exception."""

    def __init__(
        self,
        signals: tuple[bool, bool, bool] | None = None,
        error: Exception | None = None,
    ) -> None:
        self._signals = signals
        self._error = error

    def detect(self, text_sample: str, title: str | None) -> tuple[bool, bool, bool]:
        """Return configured signals, raise configured exception, or return default false signals."""
        if self._error is not None:
            raise self._error
        if self._signals is not None:
            return self._signals
        return False, False, False
