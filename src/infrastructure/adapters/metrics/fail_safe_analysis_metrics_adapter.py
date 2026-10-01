from collections.abc import Callable
from logging import getLogger

from src.domain.dtos.ai_interaction_dto import AiInteractionDTO
from src.domain.dtos.analysis_completion_dto import AnalysisCompletionDTO
from src.domain.dtos.analysis_start_dto import AnalysisStartDTO
from src.domain.dtos.stage_duration_dto import StageDurationDTO
from src.domain.metrics.analysis_metrics_port import AnalysisMetricsPort

logger = getLogger(__name__)


class FailSafeAnalysisMetricsAdapter(AnalysisMetricsPort):
    """Decorator adapter for AnalysisMetricsPort ensuring telemetry failures never break document analysis."""

    def __init__(self, analysis_metrics_port: AnalysisMetricsPort) -> None:
        self._analysis_metrics_port = analysis_metrics_port

    def record_analysis_start(self, start_data: AnalysisStartDTO) -> None:
        """Record the start of an analysis, suppressing and logging any errors."""
        self._execute_safely(
            operation_name="record_analysis_start",
            action=lambda: self._analysis_metrics_port.record_analysis_start(start_data=start_data),
        )

    def record_stage_duration(self, stage_duration: StageDurationDTO) -> None:
        """Record the duration of an analysis stage, suppressing and logging any errors."""
        self._execute_safely(
            operation_name="record_stage_duration",
            action=lambda: self._analysis_metrics_port.record_stage_duration(
                stage_duration=stage_duration
            ),
        )

    def record_ai_interaction(self, ai_interaction: AiInteractionDTO) -> None:
        """Record an external AI interaction event, suppressing and logging any errors."""
        self._execute_safely(
            operation_name="record_ai_interaction",
            action=lambda: self._analysis_metrics_port.record_ai_interaction(
                ai_interaction=ai_interaction
            ),
        )

    def record_analysis_completion(self, completion_data: AnalysisCompletionDTO) -> None:
        """Record the completion of an analysis, suppressing and logging any errors."""
        self._execute_safely(
            operation_name="record_analysis_completion",
            action=lambda: self._analysis_metrics_port.record_analysis_completion(
                completion_data=completion_data
            ),
        )

    def _execute_safely(self, operation_name: str, action: Callable[[], None]) -> None:
        try:
            action()
        except Exception:
            logger.warning(
                "Analysis metrics recording failed during %s",
                operation_name,
                exc_info=True,
            )
