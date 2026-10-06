from src.domain.exceptions.base_src_error import SrcBaseWarning


class AnalysisError(SrcBaseWarning):
    """Base class for all analysis-related exceptions."""


class AnalysisCancelled(AnalysisError):
    """Raised when an analysis is canceled because the client disconnected."""

    MESSAGE = "The analysis was cancelled because the client disconnected."
