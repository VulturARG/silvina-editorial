from abc import ABC, abstractmethod

from src.domain.dtos.ai_interaction_dto import AiInteractionDTO
from src.domain.dtos.analysis_completion_dto import AnalysisCompletionDTO
from src.domain.dtos.analysis_start_dto import AnalysisStartDTO
from src.domain.dtos.stage_duration_dto import StageDurationDTO


class AnalysisMetricsPort(ABC):
    """Port for recording analysis lifecycle metrics and AI interaction telemetry."""

    @abstractmethod
    def record_analysis_start(self, start_data: AnalysisStartDTO) -> None:
        """Record the beginning of a document analysis."""

    @abstractmethod
    def record_stage_duration(self, stage_duration: StageDurationDTO) -> None:
        """Record the execution duration of an analysis stage in milliseconds."""

    @abstractmethod
    def record_ai_interaction(self, ai_interaction: AiInteractionDTO) -> None:
        """Record telemetry of an external AI interaction."""

    @abstractmethod
    def record_analysis_completion(self, completion_data: AnalysisCompletionDTO) -> None:
        """Record the final summary and outcome of a document analysis."""
