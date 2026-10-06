from src.domain.metrics.analysis_cancellation_port import AnalysisCancellationPort


class FakeAnalysisCancellationPort(AnalysisCancellationPort):
    """In-memory test double for AnalysisCancellationPort storing cancellation state."""

    def __init__(self) -> None:
        self._is_bound: bool = False
        self._is_requested: bool = False

    def bind_new_cancellation_signal(self) -> None:
        """Bind a fresh, not-requested cancellation signal in memory."""
        self._is_bound = True
        self._is_requested = False

    def request_cancellation(self) -> None:
        """Mark cancellation as requested if a signal is currently bound."""
        if self._is_bound:
            self._is_requested = True

    def is_cancellation_requested(self) -> bool:
        """Return True only when a signal is bound and cancellation was requested."""
        return self._is_bound and self._is_requested

    def clear_cancellation_signal(self) -> None:
        """Clear the cancellation signal in memory."""
        self._is_bound = False
        self._is_requested = False
