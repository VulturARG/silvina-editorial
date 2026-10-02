from abc import ABC, abstractmethod


class AnalysisCancellationPort(ABC):
    """Port for managing analysis cancellation signaling in the current execution context."""

    @abstractmethod
    def bind_new_cancellation_signal(self) -> None:
        """Bind a fresh, not-requested cancellation signal to the current execution context."""

    @abstractmethod
    def request_cancellation(self) -> None:
        """Request cancellation of the active analysis in the current execution context."""

    @abstractmethod
    def is_cancellation_requested(self) -> bool:
        """Return whether cancellation has been requested for the active analysis."""

    @abstractmethod
    def clear_cancellation_signal(self) -> None:
        """Remove the cancellation signal from the current execution context."""
