from time import sleep
from unittest import TestCase
from unittest.mock import MagicMock

from src.domain.dtos.report_input_dto import ReportInputDTO
from src.domain.enums.analysis_stage import AnalysisStage
from src.domain.enums.article_type import ArticleType
from src.domain.enums.execution_status import ExecutionStatus
from src.domain.enums.publication_verdict import PublicationVerdict
from src.domain.metrics.analysis_metrics_recorder import AnalysisMetricsRecorder
from src.domain.metrics.analysis_tracker import AnalysisTracker
from src.domain.tests.metrics.fake_analysis_context_port import FakeAnalysisContextPort
from src.domain.tests.metrics.fake_analysis_metrics_port import FakeAnalysisMetricsPort


def _make_report_input_dto(
    filename: str = "document.docx",
    word_count: int = 1500,
    char_count: int = 9000,
    article_type: ArticleType = ArticleType.SCIENTIFIC,
    verdict: PublicationVerdict = PublicationVerdict.APPROVED,
) -> ReportInputDTO:
    document_content = MagicMock()
    document_content.word_count = word_count
    document_content.char_count = char_count

    classification = MagicMock()
    classification.effective_structure_type = article_type

    verdict_mock = MagicMock()
    verdict_mock.verdict = verdict

    return ReportInputDTO(
        filename=filename,
        document_content=document_content,
        classification=classification,
        quality=MagicMock(),
        grammar=MagicMock(),
        structure=MagicMock(),
        citations=MagicMock(),
        apa_validation=MagicMock(),
        recommendations=[],
        verdict=verdict_mock,
        eumic_violations=[],
    )


class TestAnalysisTracker(TestCase):
    def test_track_analysis_returns_pipeline_report_unchanged(self):
        fake_metrics_port = FakeAnalysisMetricsPort()
        recorder = AnalysisMetricsRecorder(metrics_port=fake_metrics_port)
        context_port = FakeAnalysisContextPort()
        tracker = AnalysisTracker(
            metrics_recorder=recorder,
            analysis_context_port=context_port,
        )
        expected_report = _make_report_input_dto()

        result = tracker.track_analysis(
            document_name="paper.docx",
            pipeline=lambda: expected_report,
        )

        self.assertIs(result, expected_report)

    def test_track_analysis_records_start_with_base_filename_and_32_char_hex_id(self):
        fake_metrics_port = FakeAnalysisMetricsPort()
        recorder = AnalysisMetricsRecorder(metrics_port=fake_metrics_port)
        context_port = FakeAnalysisContextPort()
        tracker = AnalysisTracker(
            metrics_recorder=recorder,
            analysis_context_port=context_port,
        )

        tracker.track_analysis(
            document_name=r"C:\docs\research\paper.docx",
            pipeline=_make_report_input_dto,
        )

        self.assertEqual(len(fake_metrics_port.recorded_starts), 1)
        start_data = fake_metrics_port.recorded_starts[0]
        self.assertEqual(start_data.document_name, "paper.docx")
        self.assertEqual(len(start_data.analysis_id), 32)
        int(start_data.analysis_id, 16)

    def test_pipeline_observes_active_analysis_id_in_context_port(self):
        fake_metrics_port = FakeAnalysisMetricsPort()
        recorder = AnalysisMetricsRecorder(metrics_port=fake_metrics_port)
        context_port = FakeAnalysisContextPort()
        tracker = AnalysisTracker(
            metrics_recorder=recorder,
            analysis_context_port=context_port,
        )
        observed_ids: list[str | None] = []

        def pipeline_action() -> ReportInputDTO:
            observed_ids.append(context_port.get_analysis_id())
            return _make_report_input_dto()

        tracker.track_analysis(
            document_name="paper.docx",
            pipeline=pipeline_action,
        )

        active_id = fake_metrics_port.recorded_starts[0].analysis_id
        self.assertEqual(observed_ids, [active_id])

    def test_track_analysis_records_completion_on_success(self):
        fake_metrics_port = FakeAnalysisMetricsPort()
        recorder = AnalysisMetricsRecorder(metrics_port=fake_metrics_port)
        context_port = FakeAnalysisContextPort()
        tracker = AnalysisTracker(
            metrics_recorder=recorder,
            analysis_context_port=context_port,
        )
        report = _make_report_input_dto(
            word_count=1800,
            char_count=11000,
            article_type=ArticleType.POPULAR_SCIENCE,
            verdict=PublicationVerdict.WARNING,
        )

        def slow_pipeline() -> ReportInputDTO:
            sleep(0.02)
            return report

        tracker.track_analysis(
            document_name=r"C:\docs\paper.docx",
            pipeline=slow_pipeline,
        )

        self.assertEqual(len(fake_metrics_port.recorded_completions), 1)
        completion = fake_metrics_port.recorded_completions[0]
        start_data = fake_metrics_port.recorded_starts[0]
        self.assertEqual(completion.analysis_id, start_data.analysis_id)
        self.assertEqual(completion.document_name, "paper.docx")
        self.assertEqual(completion.status, ExecutionStatus.SUCCESS)
        self.assertEqual(completion.word_count, 1800)
        self.assertEqual(completion.char_count, 11000)
        self.assertEqual(completion.article_type, ArticleType.POPULAR_SCIENCE)
        self.assertEqual(completion.verdict, PublicationVerdict.WARNING)
        self.assertGreaterEqual(completion.total_duration_ms, 5.0)

    def test_track_analysis_clears_context_after_success(self):
        fake_metrics_port = FakeAnalysisMetricsPort()
        recorder = AnalysisMetricsRecorder(metrics_port=fake_metrics_port)
        context_port = FakeAnalysisContextPort()
        tracker = AnalysisTracker(
            metrics_recorder=recorder,
            analysis_context_port=context_port,
        )

        tracker.track_analysis(
            document_name="paper.docx",
            pipeline=_make_report_input_dto,
        )

        self.assertIsNone(context_port.get_analysis_id())

    def test_track_analysis_re_raises_pipeline_exception_records_error_completion_and_clears_context(
        self,
    ):
        fake_metrics_port = FakeAnalysisMetricsPort()
        recorder = AnalysisMetricsRecorder(metrics_port=fake_metrics_port)
        context_port = FakeAnalysisContextPort()
        tracker = AnalysisTracker(
            metrics_recorder=recorder,
            analysis_context_port=context_port,
        )
        expected_exception = RuntimeError("pipeline execution failed")

        def failing_pipeline() -> ReportInputDTO:
            raise expected_exception

        with self.assertRaises(RuntimeError) as caught:
            tracker.track_analysis(
                document_name=r"/var/uploads/paper.docx",
                pipeline=failing_pipeline,
            )

        self.assertIs(caught.exception, expected_exception)
        self.assertEqual(len(fake_metrics_port.recorded_completions), 1)
        completion = fake_metrics_port.recorded_completions[0]
        start_data = fake_metrics_port.recorded_starts[0]
        self.assertEqual(completion.analysis_id, start_data.analysis_id)
        self.assertEqual(completion.document_name, "paper.docx")
        self.assertEqual(completion.status, ExecutionStatus.ERROR)
        self.assertIsNone(completion.word_count)
        self.assertIsNone(completion.char_count)
        self.assertIsNone(completion.article_type)
        self.assertIsNone(completion.verdict)
        self.assertGreaterEqual(completion.total_duration_ms, 0.0)
        self.assertIsNone(context_port.get_analysis_id())

    def test_track_analysis_clears_context_when_recording_start_fails(self):
        fake_metrics_port = FakeAnalysisMetricsPort()
        fake_metrics_port.record_analysis_start = MagicMock(
            side_effect=RuntimeError("metrics port start failed")
        )
        recorder = AnalysisMetricsRecorder(metrics_port=fake_metrics_port)
        context_port = FakeAnalysisContextPort()
        tracker = AnalysisTracker(
            metrics_recorder=recorder,
            analysis_context_port=context_port,
        )

        with self.assertRaises(RuntimeError):
            tracker.track_analysis(
                document_name="paper.docx",
                pipeline=_make_report_input_dto,
            )

        self.assertIsNone(context_port.get_analysis_id())

    def test_two_consecutive_analyses_receive_different_analysis_ids(self):
        fake_metrics_port = FakeAnalysisMetricsPort()
        recorder = AnalysisMetricsRecorder(metrics_port=fake_metrics_port)
        context_port = FakeAnalysisContextPort()
        tracker = AnalysisTracker(
            metrics_recorder=recorder,
            analysis_context_port=context_port,
        )

        tracker.track_analysis(
            document_name="first.docx",
            pipeline=_make_report_input_dto,
        )
        tracker.track_analysis(
            document_name="second.docx",
            pipeline=_make_report_input_dto,
        )

        self.assertEqual(len(fake_metrics_port.recorded_starts), 2)
        first_id = fake_metrics_port.recorded_starts[0].analysis_id
        second_id = fake_metrics_port.recorded_starts[1].analysis_id
        self.assertNotEqual(first_id, second_id)

    def test_measure_stage_records_duration_for_active_analysis(self):
        fake_metrics_port = FakeAnalysisMetricsPort()
        recorder = AnalysisMetricsRecorder(metrics_port=fake_metrics_port)
        context_port = FakeAnalysisContextPort()
        context_port.set_analysis_id("active-analysis-123")
        tracker = AnalysisTracker(
            metrics_recorder=recorder,
            analysis_context_port=context_port,
        )

        with tracker.measure_stage(AnalysisStage.EXTRACT_CONTENT):
            sleep(0.01)

        self.assertEqual(len(fake_metrics_port.recorded_stage_durations), 1)
        stage = fake_metrics_port.recorded_stage_durations[0]
        self.assertEqual(stage.analysis_id, "active-analysis-123")
        self.assertEqual(stage.stage_name, AnalysisStage.EXTRACT_CONTENT)
        self.assertGreaterEqual(stage.duration_ms, 0.0)

    def test_measure_stage_records_duration_when_stage_body_raises_exception(self):
        fake_metrics_port = FakeAnalysisMetricsPort()
        recorder = AnalysisMetricsRecorder(metrics_port=fake_metrics_port)
        context_port = FakeAnalysisContextPort()
        context_port.set_analysis_id("active-analysis-123")
        tracker = AnalysisTracker(
            metrics_recorder=recorder,
            analysis_context_port=context_port,
        )
        expected_exception = ValueError("stage body raised")

        with self.assertRaises(ValueError) as caught:
            with tracker.measure_stage(AnalysisStage.CHECK_GRAMMAR):
                raise expected_exception

        self.assertIs(caught.exception, expected_exception)
        self.assertEqual(len(fake_metrics_port.recorded_stage_durations), 1)
        stage = fake_metrics_port.recorded_stage_durations[0]
        self.assertEqual(stage.analysis_id, "active-analysis-123")
        self.assertEqual(stage.stage_name, AnalysisStage.CHECK_GRAMMAR)
        self.assertGreaterEqual(stage.duration_ms, 0.0)

    def test_measure_stage_does_not_record_when_no_active_analysis_id(self):
        fake_metrics_port = FakeAnalysisMetricsPort()
        recorder = AnalysisMetricsRecorder(metrics_port=fake_metrics_port)
        context_port = FakeAnalysisContextPort()
        tracker = AnalysisTracker(
            metrics_recorder=recorder,
            analysis_context_port=context_port,
        )
        executed = False

        with tracker.measure_stage(AnalysisStage.VALIDATE_APA):
            executed = True

        self.assertTrue(executed)
        self.assertEqual(fake_metrics_port.recorded_stage_durations, [])

    def test_stages_measured_within_pipeline_share_analysis_id_with_start_and_completion(self):
        fake_metrics_port = FakeAnalysisMetricsPort()
        recorder = AnalysisMetricsRecorder(metrics_port=fake_metrics_port)
        context_port = FakeAnalysisContextPort()
        tracker = AnalysisTracker(
            metrics_recorder=recorder,
            analysis_context_port=context_port,
        )

        def staged_pipeline() -> ReportInputDTO:
            with tracker.measure_stage(AnalysisStage.VALIDATE_STRUCTURE):
                pass
            with tracker.measure_stage(AnalysisStage.ANALYZE_QUALITY):
                pass
            return _make_report_input_dto()

        tracker.track_analysis(
            document_name="paper.docx",
            pipeline=staged_pipeline,
        )

        start_id = fake_metrics_port.recorded_starts[0].analysis_id
        completion_id = fake_metrics_port.recorded_completions[0].analysis_id
        self.assertEqual(start_id, completion_id)
        self.assertEqual(len(fake_metrics_port.recorded_stage_durations), 2)
        self.assertEqual(fake_metrics_port.recorded_stage_durations[0].analysis_id, start_id)
        self.assertEqual(
            fake_metrics_port.recorded_stage_durations[0].stage_name,
            AnalysisStage.VALIDATE_STRUCTURE,
        )
        self.assertEqual(fake_metrics_port.recorded_stage_durations[1].analysis_id, start_id)
        self.assertEqual(
            fake_metrics_port.recorded_stage_durations[1].stage_name,
            AnalysisStage.ANALYZE_QUALITY,
        )
