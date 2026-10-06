from logging import INFO, LogRecord
from unittest import TestCase

from src.domain.tests.metrics.fake_analysis_context_port import FakeAnalysisContextPort
from src.infrastructure.config.analysis_context_log_filter import AnalysisContextLogFilter


class TestAnalysisContextLogFilter(TestCase):
    def setUp(self) -> None:
        self._fake_analysis_context_port = FakeAnalysisContextPort()
        self._filter = AnalysisContextLogFilter(self._fake_analysis_context_port)

    def test_sets_analysis_id_on_record_from_port(self) -> None:
        self._fake_analysis_context_port.set_analysis_id("analysis-123")
        record = LogRecord(
            name="test_logger",
            level=INFO,
            pathname="test_path.py",
            lineno=10,
            msg="test message",
            args=(),
            exc_info=None,
        )

        filter_result = self._filter.filter(record)

        self.assertTrue(filter_result)
        self.assertEqual(getattr(record, "analysis_id", None), "analysis-123")

    def test_uses_dash_placeholder_when_port_has_no_analysis_id(self) -> None:
        record = LogRecord(
            name="test_logger",
            level=INFO,
            pathname="test_path.py",
            lineno=10,
            msg="test message",
            args=(),
            exc_info=None,
        )

        filter_result = self._filter.filter(record)

        self.assertTrue(filter_result)
        self.assertEqual(getattr(record, "analysis_id", None), "-")

    def test_filter_always_returns_true(self) -> None:
        record_without_analysis_id = LogRecord(
            name="test_logger",
            level=INFO,
            pathname="test_path.py",
            lineno=10,
            msg="message without analysis id",
            args=(),
            exc_info=None,
        )
        self.assertTrue(self._filter.filter(record_without_analysis_id))

        self._fake_analysis_context_port.set_analysis_id("analysis-456")
        record_with_analysis_id = LogRecord(
            name="test_logger",
            level=INFO,
            pathname="test_path.py",
            lineno=20,
            msg="message with analysis id",
            args=(),
            exc_info=None,
        )
        self.assertTrue(self._filter.filter(record_with_analysis_id))

    def test_keeps_record_message_untouched(self) -> None:
        original_message = "original unformatted message"
        record = LogRecord(
            name="test_logger",
            level=INFO,
            pathname="test_path.py",
            lineno=10,
            msg=original_message,
            args=(),
            exc_info=None,
        )

        self._filter.filter(record)

        self.assertEqual(record.msg, original_message)
        self.assertEqual(record.getMessage(), original_message)
