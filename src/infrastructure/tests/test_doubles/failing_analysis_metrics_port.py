from src.domain.dtos.ai_interaction_dto import AiInteractionDTO
from src.domain.dtos.analysis_completion_dto import AnalysisCompletionDTO
from src.domain.dtos.analysis_start_dto import AnalysisStartDTO
from src.domain.dtos.stage_duration_dto import StageDurationDTO
from src.domain.metrics.analysis_metrics_port import AnalysisMetricsPort


class FailingAnalysisMetricsPort(AnalysisMetricsPort):
    """Test double for AnalysisMetricsPort that raises a preconfigured exception on all operations."""

    def __init__(self, exception: Exception) -> None:
        self._exception = exception

    def record_analysis_start(self, start_data: AnalysisStartDTO) -> None:
        """Raise the preconfigured exception on recording analysis start."""
        raise self._exception

    def record_stage_duration(self, stage_duration: StageDurationDTO) -> None:
        """Raise the preconfigured exception on recording stage duration."""
        raise self._exception

    def record_ai_interaction(self, ai_interaction: AiInteractionDTO) -> None:
        """Raise the preconfigured exception on recording AI interaction."""
        raise self._exception

    def record_analysis_completion(self, completion_data: AnalysisCompletionDTO) -> None:
        """Raise the preconfigured exception on recording analysis completion."""
        raise self._exception
