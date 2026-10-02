from src.domain.metrics.analysis_cancellation_port import AnalysisCancellationPort
from src.infrastructure.adapters.metrics.analysis_cancellation_adapter import (
    AnalysisCancellationAdapter,
)


class AnalysisCancellationWiring:
    """Dependency wiring assembling the analysis cancellation port."""

    def get_analysis_cancellation_port(self) -> AnalysisCancellationPort:
        """Return an analysis cancellation port implementation."""
        return AnalysisCancellationAdapter()
