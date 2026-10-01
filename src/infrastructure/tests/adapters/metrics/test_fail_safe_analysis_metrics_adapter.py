from unittest import TestCase
from unittest.mock import MagicMock

from src.domain.dtos.ai_interaction_dto import AiInteractionDTO
from src.domain.dtos.analysis_completion_dto import AnalysisCompletionDTO
from src.domain.dtos.analysis_start_dto import AnalysisStartDTO
from src.domain.dtos.stage_duration_dto import StageDurationDTO
from src.domain.enums.ai_provider import AiProvider
from src.domain.enums.ai_purpose import AiPurpose
from src.domain.enums.analysis_stage import AnalysisStage
from src.domain.enums.article_type import ArticleType
from src.domain.enums.execution_status import ExecutionStatus
from src.domain.enums.publication_verdict import PublicationVerdict
from src.domain.metrics.analysis_metrics_port import AnalysisMetricsPort
from src.domain.tests.metrics.fake_analysis_metrics_port import FakeAnalysisMetricsPort
from src.infrastructure.adapters.metrics.fail_safe_analysis_metrics_adapter import (
    FailSafeAnalysisMetricsAdapter,
)
from src.infrastructure.tests.test_doubles.failing_analysis_metrics_port import (
    FailingAnalysisMetricsPort,
)

_LOGGER_NAME = "src.infrastructure.adapters.metrics.fail_safe_analysis_metrics_adapter"


class TestFailSafeAnalysisMetricsAdapter(TestCase):
    def test_is_instance_of_analysis_metrics_port(self):
        fake_port = FakeAnalysisMetricsPort()
        adapter = FailSafeAnalysisMetricsAdapter(analysis_metrics_port=fake_port)

        self.assertIsInstance(adapter, AnalysisMetricsPort)

    def test_record_analysis_start_delegates_to_wrapped_port(self):
        fake_port = FakeAnalysisMetricsPort()
        adapter = FailSafeAnalysisMetricsAdapter(analysis_metrics_port=fake_port)
        start_data = AnalysisStartDTO(
            analysis_id="analysis-123",
            document_name="sample.docx",
        )

        adapter.record_analysis_start(start_data=start_data)

        self.assertEqual(fake_port.recorded_starts, [start_data])

    def test_record_stage_duration_delegates_to_wrapped_port(self):
        fake_port = FakeAnalysisMetricsPort()
        adapter = FailSafeAnalysisMetricsAdapter(analysis_metrics_port=fake_port)
        stage_duration = StageDurationDTO(
            analysis_id="analysis-123",
            stage_name=AnalysisStage.ANALYZE_QUALITY,
            duration_ms=45.2,
        )

        adapter.record_stage_duration(stage_duration=stage_duration)

        self.assertEqual(fake_port.recorded_stage_durations, [stage_duration])

    def test_record_ai_interaction_delegates_to_wrapped_port(self):
        fake_port = FakeAnalysisMetricsPort()
        adapter = FailSafeAnalysisMetricsAdapter(analysis_metrics_port=fake_port)
        ai_interaction = AiInteractionDTO(
            analysis_id="analysis-123",
            provider=AiProvider.OLLAMA,
            purpose=AiPurpose.ARTICLE_CLASSIFICATION,
            model_name="mistral",
            input_payload="analysis prompt text",
            output_payload="classification output text",
            duration_ms=210.0,
            status=ExecutionStatus.SUCCESS,
        )

        adapter.record_ai_interaction(ai_interaction=ai_interaction)

        self.assertEqual(fake_port.recorded_ai_interactions, [ai_interaction])

    def test_record_analysis_completion_delegates_to_wrapped_port(self):
        fake_port = FakeAnalysisMetricsPort()
        adapter = FailSafeAnalysisMetricsAdapter(analysis_metrics_port=fake_port)
        completion_data = AnalysisCompletionDTO(
            analysis_id="analysis-123",
            document_name="sample.docx",
            word_count=1200,
            char_count=7000,
            article_type=ArticleType.SCIENTIFIC,
            verdict=PublicationVerdict.APPROVED,
            total_duration_ms=850.0,
            status=ExecutionStatus.SUCCESS,
        )

        adapter.record_analysis_completion(completion_data=completion_data)

        self.assertEqual(fake_port.recorded_completions, [completion_data])

    def test_record_analysis_start_suppresses_exception_and_logs_warning(self):
        failing_port = FailingAnalysisMetricsPort(exception=RuntimeError("database disk is full"))
        adapter = FailSafeAnalysisMetricsAdapter(analysis_metrics_port=failing_port)
        start_data = AnalysisStartDTO(
            analysis_id="analysis-123",
            document_name="confidential_manuscript.docx",
        )

        with self.assertLogs(_LOGGER_NAME, level="WARNING") as captured_logs:
            adapter.record_analysis_start(start_data=start_data)

        self.assertTrue(any("record_analysis_start" in message for message in captured_logs.output))
        self.assertFalse(
            any("confidential_manuscript.docx" in message for message in captured_logs.output)
        )

    def test_record_stage_duration_suppresses_exception_and_logs_warning(self):
        failing_port = FailingAnalysisMetricsPort(exception=RuntimeError("database disk is full"))
        adapter = FailSafeAnalysisMetricsAdapter(analysis_metrics_port=failing_port)
        stage_duration = StageDurationDTO(
            analysis_id="analysis-123",
            stage_name=AnalysisStage.CHECK_GRAMMAR,
            duration_ms=12.5,
        )

        with self.assertLogs(_LOGGER_NAME, level="WARNING") as captured_logs:
            adapter.record_stage_duration(stage_duration=stage_duration)

        self.assertTrue(any("record_stage_duration" in message for message in captured_logs.output))

    def test_record_ai_interaction_suppresses_exception_and_logs_warning_without_payload(self):
        failing_port = FailingAnalysisMetricsPort(exception=RuntimeError("database disk is full"))
        adapter = FailSafeAnalysisMetricsAdapter(analysis_metrics_port=failing_port)
        ai_interaction = AiInteractionDTO(
            analysis_id="analysis-123",
            provider=AiProvider.OLLAMA,
            purpose=AiPurpose.ARTICLE_CLASSIFICATION,
            model_name="mistral",
            input_payload="ultra_secret_prompt_payload",
            output_payload="ultra_secret_output_payload",
            duration_ms=150.0,
            status=ExecutionStatus.SUCCESS,
        )

        with self.assertLogs(_LOGGER_NAME, level="WARNING") as captured_logs:
            adapter.record_ai_interaction(ai_interaction=ai_interaction)

        self.assertTrue(any("record_ai_interaction" in message for message in captured_logs.output))
        self.assertFalse(
            any("ultra_secret_prompt_payload" in message for message in captured_logs.output)
        )
        self.assertFalse(
            any("ultra_secret_output_payload" in message for message in captured_logs.output)
        )

    def test_record_analysis_completion_suppresses_exception_and_logs_warning(self):
        failing_port = FailingAnalysisMetricsPort(exception=RuntimeError("database disk is full"))
        adapter = FailSafeAnalysisMetricsAdapter(analysis_metrics_port=failing_port)
        completion_data = AnalysisCompletionDTO(
            analysis_id="analysis-123",
            document_name="confidential_manuscript.docx",
            word_count=500,
            char_count=3500,
            article_type=ArticleType.POPULAR_SCIENCE,
            verdict=PublicationVerdict.CRITICAL,
            total_duration_ms=300.0,
            status=ExecutionStatus.ERROR,
        )

        with self.assertLogs(_LOGGER_NAME, level="WARNING") as captured_logs:
            adapter.record_analysis_completion(completion_data=completion_data)

        self.assertTrue(
            any("record_analysis_completion" in message for message in captured_logs.output)
        )

    def test_failing_operation_does_not_prevent_subsequent_operations_from_reaching_wrapped_port(
        self,
    ):
        wrapped_port = MagicMock(spec=AnalysisMetricsPort)
        wrapped_port.record_analysis_start.side_effect = RuntimeError("start failed")
        adapter = FailSafeAnalysisMetricsAdapter(analysis_metrics_port=wrapped_port)
        start_data = AnalysisStartDTO(
            analysis_id="analysis-123",
            document_name="sample.docx",
        )
        completion_data = AnalysisCompletionDTO(
            analysis_id="analysis-123",
            document_name="sample.docx",
            word_count=100,
            char_count=600,
            article_type=ArticleType.SCIENTIFIC,
            verdict=PublicationVerdict.APPROVED,
            total_duration_ms=50.0,
            status=ExecutionStatus.SUCCESS,
        )

        with self.assertLogs(_LOGGER_NAME, level="WARNING"):
            adapter.record_analysis_start(start_data=start_data)

        adapter.record_analysis_completion(completion_data=completion_data)

        wrapped_port.record_analysis_completion.assert_called_once_with(
            completion_data=completion_data
        )
