from logging import Filter, LogRecord

from src.domain.metrics.analysis_context_port import AnalysisContextPort

_NO_ANALYSIS_PLACEHOLDER = "-"


class AnalysisContextLogFilter(Filter):
    """Filter that enriches log records with the active analysis identifier."""

    def __init__(self, analysis_context_port: AnalysisContextPort) -> None:
        """Initialize the filter with an analysis context port."""
        super().__init__()
        self._analysis_context_port = analysis_context_port

    def filter(self, record: LogRecord) -> bool:
        """Enrich the log record with the current analysis identifier."""
        analysis_id = self._analysis_context_port.get_analysis_id()
        record.analysis_id = analysis_id if analysis_id is not None else _NO_ANALYSIS_PLACEHOLDER
        return True
