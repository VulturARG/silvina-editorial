from src.domain.exceptions.base_src_error import SrcBaseWarning


class AnalysisCancelled(SrcBaseWarning):
    """Raised when an analysis is cancelled because the client disconnected."""

    MESSAGE = "The analysis was cancelled because the client disconnected."
