from abc import ABC, abstractmethod


class ResearchIntentDetectorPort(ABC):
    """Port for detecting research intent signals from text samples and titles."""

    @abstractmethod
    def detect(self, text_sample: str, title: str | None) -> tuple[bool, bool, bool]:
        """Detect research intent signals and return a tuple of boolean flags."""
