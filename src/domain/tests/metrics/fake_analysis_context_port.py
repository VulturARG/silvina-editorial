from src.domain.metrics.analysis_context_port import AnalysisContextPort


class FakeAnalysisContextPort(AnalysisContextPort):
    """In-memory test double for AnalysisContextPort storing the analysis identifier."""

    def __init__(self) -> None:
        self._analysis_id: str | None = None

    def get_analysis_id(self) -> str | None:
        """Return the currently stored analysis identifier."""
        return self._analysis_id

    def set_analysis_id(self, analysis_id: str) -> None:
        """Store the given analysis identifier in memory."""
        self._analysis_id = analysis_id

    def clear_analysis_id(self) -> None:
        """Clear the stored analysis identifier."""
        self._analysis_id = None
