from abc import ABC, abstractmethod


class AnalysisContextPort(ABC):
    """Port for managing the active analysis identifier in the current execution context."""

    @abstractmethod
    def get_analysis_id(self) -> str | None:
        """Return the analysis identifier active in the current execution context, if any."""

    @abstractmethod
    def set_analysis_id(self, analysis_id: str) -> None:
        """Bind the given analysis identifier to the current execution context."""

    @abstractmethod
    def clear_analysis_id(self) -> None:
        """Remove the analysis identifier from the current execution context."""
