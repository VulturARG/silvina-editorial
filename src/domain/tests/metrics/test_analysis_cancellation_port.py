from unittest import TestCase

from src.domain.metrics.analysis_cancellation_port import AnalysisCancellationPort
from src.domain.tests.metrics.fake_analysis_cancellation_port import (
    FakeAnalysisCancellationPort,
)


class TestAnalysisCancellationPort(TestCase):
    def test_direct_instantiation_raises_type_error(self) -> None:
        port_class: type = AnalysisCancellationPort
        with self.assertRaises(TypeError):
            port_class()

    def test_fake_is_instance_of_analysis_cancellation_port(self) -> None:
        fake_port = FakeAnalysisCancellationPort()
        self.assertIsInstance(fake_port, AnalysisCancellationPort)

    def test_fake_returns_false_when_nothing_bound(self) -> None:
        fake_port = FakeAnalysisCancellationPort()
        self.assertFalse(fake_port.is_cancellation_requested())

    def test_fake_request_cancellation_is_noop_when_not_bound(self) -> None:
        fake_port = FakeAnalysisCancellationPort()
        fake_port.request_cancellation()
        self.assertFalse(fake_port.is_cancellation_requested())

    def test_fake_bind_creates_fresh_unrequested_signal(self) -> None:
        fake_port = FakeAnalysisCancellationPort()
        fake_port.bind_new_cancellation_signal()
        self.assertFalse(fake_port.is_cancellation_requested())

    def test_fake_request_cancellation_sets_flag_when_bound(self) -> None:
        fake_port = FakeAnalysisCancellationPort()
        fake_port.bind_new_cancellation_signal()
        fake_port.request_cancellation()
        self.assertTrue(fake_port.is_cancellation_requested())

    def test_fake_clear_cancellation_signal_resets_state(self) -> None:
        fake_port = FakeAnalysisCancellationPort()
        fake_port.bind_new_cancellation_signal()
        fake_port.request_cancellation()
        fake_port.clear_cancellation_signal()
        self.assertFalse(fake_port.is_cancellation_requested())

    def test_fake_bind_after_requested_creates_fresh_unrequested_signal(self) -> None:
        fake_port = FakeAnalysisCancellationPort()
        fake_port.bind_new_cancellation_signal()
        fake_port.request_cancellation()
        fake_port.bind_new_cancellation_signal()
        self.assertFalse(fake_port.is_cancellation_requested())
