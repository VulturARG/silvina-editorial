from collections.abc import Callable, Iterator
from contextlib import contextmanager
from logging import getLogger
from pathlib import PurePath
from time import perf_counter
from typing import Any, TypeVar
from uuid import uuid4

from src.domain.dtos.analysis_completion_dto import AnalysisCompletionDTO
from src.domain.dtos.analysis_start_dto import AnalysisStartDTO
from src.domain.dtos.report_input_dto import ReportInputDTO
from src.domain.dtos.stage_duration_dto import StageDurationDTO
from src.domain.enums.analysis_stage import AnalysisStage
from src.domain.enums.execution_status import ExecutionStatus
from src.domain.exceptions.analysis_errors import AnalysisCancelled
from src.domain.metrics.analysis_cancellation_port import AnalysisCancellationPort
from src.domain.metrics.analysis_context_port import AnalysisContextPort
from src.domain.metrics.analysis_metrics_recorder import AnalysisMetricsRecorder

StageResult = TypeVar("StageResult")

logger = getLogger(__name__)

_ANALYSIS_FAILURE_LOG_FORMAT = "Analysis failed with %s after %.1f ms"
_ANALYSIS_CANCELLATION_LOG_FORMAT = "Analysis cancelled after %.1f ms"


class AnalysisTracker:
    """Domain service coordinating analysis lifecycle tracking, correlation identifiers, and stage latency measurements."""

    def __init__(
        self,
        metrics_recorder: AnalysisMetricsRecorder,
        analysis_context_port: AnalysisContextPort,
        analysis_cancellation_port: AnalysisCancellationPort,
    ) -> None:
        self._metrics_recorder = metrics_recorder
        self._analysis_context_port = analysis_context_port
        self._analysis_cancellation_port = analysis_cancellation_port

    def track_analysis(
        self,
        document_name: str,
        pipeline: Callable[[], ReportInputDTO],
    ) -> ReportInputDTO:
        """Execute an analysis pipeline within a tracked lifecycle, recording start and completion telemetry."""
        analysis_id = uuid4().hex
        base_name = PurePath(document_name).name
        try:
            self._analysis_context_port.set_analysis_id(analysis_id)
            self._metrics_recorder.start_analysis(
                start_data=AnalysisStartDTO(
                    analysis_id=analysis_id,
                    document_name=base_name,
                )
            )
            start_time = perf_counter()
            try:
                report = pipeline()
            except AnalysisCancelled:
                duration_ms = (perf_counter() - start_time) * 1000
                logger.info(
                    _ANALYSIS_CANCELLATION_LOG_FORMAT,
                    duration_ms,
                )
                self._record_cancellation(
                    analysis_id=analysis_id,
                    document_name=base_name,
                    duration_ms=duration_ms,
                )
                raise
            except Exception as exception:
                duration_ms = (perf_counter() - start_time) * 1000
                logger.error(
                    _ANALYSIS_FAILURE_LOG_FORMAT,
                    type(exception).__name__,
                    duration_ms,
                )
                self._record_failure(
                    analysis_id=analysis_id,
                    document_name=base_name,
                    duration_ms=duration_ms,
                )
                raise

            duration_ms = (perf_counter() - start_time) * 1000
            self._record_success(
                analysis_id=analysis_id,
                document_name=base_name,
                duration_ms=duration_ms,
                report=report,
            )
            return report
        finally:
            self._analysis_cancellation_port.clear_cancellation_signal()
            self._analysis_context_port.clear_analysis_id()

    @contextmanager
    def measure_stage(self, stage_name: AnalysisStage) -> Iterator[None]:
        """Measure the execution time of an analysis stage and record it if an analysis is active."""
        analysis_id = self._analysis_context_port.get_analysis_id()
        start_time = perf_counter()
        try:
            yield
        finally:
            if analysis_id is not None:
                duration_ms = (perf_counter() - start_time) * 1000
                stage_duration = StageDurationDTO(
                    analysis_id=analysis_id,
                    stage_name=stage_name,
                    duration_ms=duration_ms,
                )
                self._metrics_recorder.record_stage_duration(stage_duration=stage_duration)

    def track_stage(
        self,
        stage_name: AnalysisStage,
        operation: Callable[..., StageResult],
        **arguments: Any,
    ) -> StageResult:
        """Run the operation with the given keyword arguments, measure its duration as the given stage, and return the operation's result."""
        if self._analysis_cancellation_port.is_cancellation_requested():
            raise AnalysisCancelled()
        with self.measure_stage(stage_name=stage_name):
            return operation(**arguments)

    def _record_success(
        self,
        analysis_id: str,
        document_name: str,
        duration_ms: float,
        report: ReportInputDTO,
    ) -> None:
        completion_data = AnalysisCompletionDTO(
            analysis_id=analysis_id,
            document_name=document_name,
            word_count=report.document_content.word_count,
            char_count=report.document_content.char_count,
            article_type=report.classification.effective_structure_type,
            verdict=report.verdict.verdict,
            total_duration_ms=duration_ms,
            status=ExecutionStatus.SUCCESS,
        )
        self._metrics_recorder.complete_analysis(completion_data=completion_data)

    def _record_cancellation(
        self,
        analysis_id: str,
        document_name: str,
        duration_ms: float,
    ) -> None:
        completion_data = AnalysisCompletionDTO(
            analysis_id=analysis_id,
            document_name=document_name,
            word_count=None,
            char_count=None,
            article_type=None,
            verdict=None,
            total_duration_ms=duration_ms,
            status=ExecutionStatus.CANCELLED,
        )
        self._metrics_recorder.complete_analysis(completion_data=completion_data)

    def _record_failure(
        self,
        analysis_id: str,
        document_name: str,
        duration_ms: float,
    ) -> None:
        completion_data = AnalysisCompletionDTO(
            analysis_id=analysis_id,
            document_name=document_name,
            word_count=None,
            char_count=None,
            article_type=None,
            verdict=None,
            total_duration_ms=duration_ms,
            status=ExecutionStatus.ERROR,
        )
        self._metrics_recorder.complete_analysis(completion_data=completion_data)
