from contextvars import ContextVar
from threading import Event

from src.domain.metrics.analysis_cancellation_port import AnalysisCancellationPort


class AnalysisCancellationAdapter(AnalysisCancellationPort):
    """Adapter managing analysis cancellation signaling via Python's native contextvars and threading events."""

    _active_cancellation_signal: ContextVar[Event | None] = ContextVar(
        "active_cancellation_signal", default=None
    )

    def bind_new_cancellation_signal(self) -> None:
        """Bind a fresh, not-requested cancellation signal to the current execution context."""
        self._active_cancellation_signal.set(Event())

    def request_cancellation(self) -> None:
        """Request cancellation of the active analysis in the current execution context."""
        signal = self._active_cancellation_signal.get()
        if signal is not None:
            signal.set()

    def is_cancellation_requested(self) -> bool:
        """Return whether cancellation has been requested for the active analysis."""
        signal = self._active_cancellation_signal.get()
        if signal is None:
            return False
        return signal.is_set()

    def clear_cancellation_signal(self) -> None:
        """Remove the cancellation signal from the current execution context."""
        self._active_cancellation_signal.set(None)
