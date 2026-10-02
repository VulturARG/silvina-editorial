from src.domain.dtos.ai_interaction_dto import AiInteractionDTO
from src.domain.dtos.analysis_completion_dto import AnalysisCompletionDTO
from src.domain.dtos.analysis_start_dto import AnalysisStartDTO
from src.domain.dtos.stage_duration_dto import StageDurationDTO
from src.domain.metrics.analysis_metrics_port import AnalysisMetricsPort


class FakeAnalysisMetricsPort(AnalysisMetricsPort):
    """In-memory test double for AnalysisMetricsPort storing recorded events."""

    def __init__(self) -> None:
        self.recorded_starts: list[AnalysisStartDTO] = []
        self.recorded_stage_durations: list[StageDurationDTO] = []
        self.recorded_ai_interactions: list[AiInteractionDTO] = []
        self.recorded_completions: list[AnalysisCompletionDTO] = []

    def record_analysis_start(self, start_data: AnalysisStartDTO) -> None:
        """Store the start event data in memory."""
        self.recorded_starts.append(start_data)

    def record_stage_duration(self, stage_duration: StageDurationDTO) -> None:
        """Store the stage duration event data in memory."""
        self.recorded_stage_durations.append(stage_duration)

    def record_ai_interaction(self, ai_interaction: AiInteractionDTO) -> None:
        """Store the AI interaction event data in memory."""
        self.recorded_ai_interactions.append(ai_interaction)

    def record_analysis_completion(self, completion_data: AnalysisCompletionDTO) -> None:
        """Store the analysis completion event data in memory."""
        self.recorded_completions.append(completion_data)
