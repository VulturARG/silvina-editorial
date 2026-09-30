from unittest import TestCase

from src.domain.dtos.ai_interaction_dto import AiInteractionDTO
from src.domain.dtos.analysis_completion_dto import AnalysisCompletionDTO
from src.domain.dtos.analysis_start_dto import AnalysisStartDTO
from src.domain.dtos.stage_duration_dto import StageDurationDTO
from src.domain.metrics.analysis_metrics_port import AnalysisMetricsPort
from src.domain.tests.metrics.fake_analysis_metrics_port import FakeAnalysisMetricsPort


class TestAnalysisMetricsPort(TestCase):
    def test_direct_instantiation_raises_type_error(self):
        port_class = AnalysisMetricsPort
        with self.assertRaises(TypeError):
            port_class()

    def test_fake_is_subclass_of_analysis_metrics_port(self):
        fake_port = FakeAnalysisMetricsPort()
        self.assertIsInstance(fake_port, AnalysisMetricsPort)

    def test_fake_records_analysis_start(self):
        fake_port = FakeAnalysisMetricsPort()
        start_data = AnalysisStartDTO(
            analysis_id="analysis-123",
            document_name="doc.docx",
        )
        fake_port.record_analysis_start(start_data=start_data)
        self.assertEqual(fake_port.recorded_starts, [start_data])

    def test_fake_records_stage_duration(self):
        fake_port = FakeAnalysisMetricsPort()
        stage_duration = StageDurationDTO(
            analysis_id="analysis-123",
            stage_name="content_extraction",
            duration_ms=150.5,
        )
        fake_port.record_stage_duration(stage_duration=stage_duration)
        self.assertEqual(fake_port.recorded_stage_durations, [stage_duration])

    def test_fake_records_ai_interaction(self):
        fake_port = FakeAnalysisMetricsPort()
        ai_interaction = AiInteractionDTO(
            analysis_id="analysis-123",
            provider="ollama",
            purpose="classification",
            model_name="mistral",
            input_payload="prompt text",
            output_payload="response text",
            duration_ms=320.0,
            status="success",
        )
        fake_port.record_ai_interaction(ai_interaction=ai_interaction)
        self.assertEqual(fake_port.recorded_ai_interactions, [ai_interaction])

    def test_fake_records_analysis_completion(self):
        fake_port = FakeAnalysisMetricsPort()
        completion_data = AnalysisCompletionDTO(
            analysis_id="analysis-123",
            document_name="doc.docx",
            word_count=1200,
            char_count=7500,
            article_type="Científico",
            verdict="PUBLICABLE",
            total_duration_ms=1850.2,
            status="completed",
        )
        fake_port.record_analysis_completion(completion_data=completion_data)
        self.assertEqual(fake_port.recorded_completions, [completion_data])
