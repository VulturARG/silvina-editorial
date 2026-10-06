from src.domain.dtos.ai_interaction_dto import AiInteractionDTO
from src.domain.dtos.analysis_completion_dto import AnalysisCompletionDTO
from src.domain.dtos.analysis_start_dto import AnalysisStartDTO
from src.domain.dtos.stage_duration_dto import StageDurationDTO
from src.domain.metrics.analysis_metrics_port import AnalysisMetricsPort


class AnalysisMetricsRecorder:
    """Domain service for orchestrating analysis metrics and AI telemetry recording."""

    def __init__(self, metrics_port: AnalysisMetricsPort) -> None:
        self._metrics_port = metrics_port

    def start_analysis(self, start_data: AnalysisStartDTO) -> None:
        """Record the start of a document analysis."""
        self._metrics_port.record_analysis_start(start_data=start_data)

    def record_stage_duration(self, stage_duration: StageDurationDTO) -> None:
        """Record the duration of an analysis stage."""
        self._metrics_port.record_stage_duration(stage_duration=stage_duration)

    def record_ai_interaction(self, ai_interaction: AiInteractionDTO) -> None:
        """Record an external AI interaction event."""
        self._metrics_port.record_ai_interaction(ai_interaction=ai_interaction)

    def complete_analysis(self, completion_data: AnalysisCompletionDTO) -> None:
        """Record the completion summary of a document analysis."""
        self._metrics_port.record_analysis_completion(completion_data=completion_data)
