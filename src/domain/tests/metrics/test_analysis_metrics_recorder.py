from unittest import TestCase

from src.domain.dtos.ai_interaction_dto import AiInteractionDTO
from src.domain.dtos.analysis_completion_dto import AnalysisCompletionDTO
from src.domain.dtos.analysis_start_dto import AnalysisStartDTO
from src.domain.dtos.stage_duration_dto import StageDurationDTO
from src.domain.enums.article_type import ArticleType
from src.domain.enums.execution_status import ExecutionStatus
from src.domain.enums.publication_verdict import PublicationVerdict
from src.domain.metrics.analysis_metrics_recorder import AnalysisMetricsRecorder
from src.domain.tests.metrics.fake_analysis_metrics_port import FakeAnalysisMetricsPort


class TestAnalysisMetricsRecorder(TestCase):
    def test_start_analysis_delegates_to_metrics_port(self):
        fake_port = FakeAnalysisMetricsPort()
        recorder = AnalysisMetricsRecorder(metrics_port=fake_port)
        start_data = AnalysisStartDTO(
            analysis_id="analysis-123",
            document_name="doc.docx",
        )
        recorder.start_analysis(start_data=start_data)
        self.assertEqual(fake_port.recorded_starts, [start_data])

    def test_record_stage_duration_delegates_to_metrics_port(self):
        fake_port = FakeAnalysisMetricsPort()
        recorder = AnalysisMetricsRecorder(metrics_port=fake_port)
        stage_duration = StageDurationDTO(
            analysis_id="analysis-123",
            stage_name="content_extraction",
            duration_ms=125.4,
        )
        recorder.record_stage_duration(stage_duration=stage_duration)
        self.assertEqual(fake_port.recorded_stage_durations, [stage_duration])

    def test_record_ai_interaction_delegates_to_metrics_port(self):
        fake_port = FakeAnalysisMetricsPort()
        recorder = AnalysisMetricsRecorder(metrics_port=fake_port)
        ai_interaction = AiInteractionDTO(
            analysis_id="analysis-123",
            provider="ollama",
            purpose="classification",
            model_name="mistral",
            input_payload="prompt text",
            output_payload="response text",
            duration_ms=320.0,
            status=ExecutionStatus.SUCCESS,
        )
        recorder.record_ai_interaction(ai_interaction=ai_interaction)
        self.assertEqual(fake_port.recorded_ai_interactions, [ai_interaction])

    def test_complete_analysis_delegates_to_metrics_port(self):
        fake_port = FakeAnalysisMetricsPort()
        recorder = AnalysisMetricsRecorder(metrics_port=fake_port)
        completion_data = AnalysisCompletionDTO(
            analysis_id="analysis-123",
            document_name="doc.docx",
            word_count=1200,
            char_count=7500,
            article_type=ArticleType.SCIENTIFIC,
            verdict=PublicationVerdict.APPROVED,
            total_duration_ms=1850.2,
            status=ExecutionStatus.SUCCESS,
        )
        recorder.complete_analysis(completion_data=completion_data)
        self.assertEqual(fake_port.recorded_completions, [completion_data])
