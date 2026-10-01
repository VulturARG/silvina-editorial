from logging import getLogger
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from src.domain.dtos.report_input_dto import ReportInputDTO
from src.domain.metrics.analysis_metrics_recorder import AnalysisMetricsRecorder
from src.domain.metrics.analysis_tracker import AnalysisTracker
from src.domain.tests.metrics.fake_analysis_metrics_port import FakeAnalysisMetricsPort
from src.infrastructure.adapters.metrics.analysis_context_adapter import AnalysisContextAdapter
from src.infrastructure.config.logging_config import LoggingConfig


class TestAnalysisFailureLogCorrelation(TestCase):
    """Integration regression tests verifying failure log records correlate with analysis identifier."""

    def setUp(self) -> None:
        self._root_logger = getLogger()
        self._initial_root_handlers = list(self._root_logger.handlers)
        self._initial_root_level = self._root_logger.level
        self._temporary_directory = TemporaryDirectory()
        self._log_file_path = str(Path(self._temporary_directory.name) / "logs" / "silvina.log")

    def tearDown(self) -> None:
        for handler in list(self._root_logger.handlers):
            if handler not in self._initial_root_handlers:
                self._root_logger.removeHandler(handler)
                handler.close()
        for handler in self._initial_root_handlers:
            if handler not in self._root_logger.handlers:
                self._root_logger.addHandler(handler)
        self._root_logger.setLevel(self._initial_root_level)
        self._temporary_directory.cleanup()

    def _flush_handlers(self) -> None:
        for handler in self._root_logger.handlers:
            handler.flush()

    def test_pipeline_failure_log_record_contains_active_analysis_identifier(self) -> None:
        analysis_context_adapter = AnalysisContextAdapter()
        fake_metrics_port = FakeAnalysisMetricsPort()
        metrics_recorder = AnalysisMetricsRecorder(metrics_port=fake_metrics_port)
        analysis_tracker = AnalysisTracker(
            metrics_recorder=metrics_recorder,
            analysis_context_port=analysis_context_adapter,
        )
        logging_config = LoggingConfig(
            log_file_path=self._log_file_path,
            log_level="INFO",
            backup_count=1,
            analysis_context_port=analysis_context_adapter,
        )
        logging_config.configure()

        def failing_pipeline() -> ReportInputDTO:
            raise RuntimeError("deliberate pipeline crash")

        with self.assertRaises(RuntimeError):
            analysis_tracker.track_analysis(
                document_name="sample_manuscript.docx",
                pipeline=failing_pipeline,
            )

        self._flush_handlers()
        log_content = Path(self._log_file_path).read_text(encoding="utf-8")

        self.assertEqual(len(fake_metrics_port.recorded_completions), 1)
        expected_analysis_id = fake_metrics_port.recorded_completions[0].analysis_id
        self.assertIsNotNone(expected_analysis_id)

        matching_log_lines = [
            line
            for line in log_content.splitlines()
            if "src.domain.metrics.analysis_tracker" in line
        ]
        self.assertEqual(len(matching_log_lines), 1)
        tracker_failure_line = matching_log_lines[0]
        self.assertIn(f"analysis_id={expected_analysis_id}", tracker_failure_line)
        self.assertNotIn("analysis_id=-", tracker_failure_line)
