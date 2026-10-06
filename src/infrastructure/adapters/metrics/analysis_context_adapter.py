from contextvars import ContextVar

from src.domain.metrics.analysis_context_port import AnalysisContextPort


class AnalysisContextAdapter(AnalysisContextPort):
    """Adapter for managing analysis context via Python's native contextvars."""

    _active_analysis_id: ContextVar[str | None] = ContextVar("active_analysis_id", default=None)

    def get_analysis_id(self) -> str | None:
        """Return the analysis identifier active in the current execution context, if any."""
        return self._active_analysis_id.get()

    def set_analysis_id(self, analysis_id: str) -> None:
        """Bind the given analysis identifier to the current execution context."""
        self._active_analysis_id.set(analysis_id)

    def clear_analysis_id(self) -> None:
        """Remove the analysis identifier from the current execution context."""
        self._active_analysis_id.set(None)
