from contextvars import copy_context
from threading import Thread
from unittest import TestCase

from src.domain.metrics.analysis_cancellation_port import AnalysisCancellationPort
from src.infrastructure.adapters.metrics.analysis_cancellation_adapter import (
    AnalysisCancellationAdapter,
)


class TestAnalysisCancellationAdapter(TestCase):
    """Unit tests verifying the behavior of native contextvar-backed analysis cancellation adapter."""

    def setUp(self) -> None:
        adapter = AnalysisCancellationAdapter()
        adapter.clear_cancellation_signal()

    def tearDown(self) -> None:
        adapter = AnalysisCancellationAdapter()
        adapter.clear_cancellation_signal()

    def test_is_instance_of_analysis_cancellation_port(self) -> None:
        adapter = AnalysisCancellationAdapter()
        self.assertIsInstance(adapter, AnalysisCancellationPort)

    def test_is_cancellation_requested_returns_false_when_unbound(self) -> None:
        adapter = AnalysisCancellationAdapter()
        self.assertFalse(adapter.is_cancellation_requested())

    def test_request_cancellation_is_noop_when_unbound(self) -> None:
        adapter = AnalysisCancellationAdapter()
        adapter.request_cancellation()
        self.assertFalse(adapter.is_cancellation_requested())

    def test_bind_new_cancellation_signal_initializes_unrequested_signal(self) -> None:
        adapter = AnalysisCancellationAdapter()
        adapter.bind_new_cancellation_signal()
        self.assertFalse(adapter.is_cancellation_requested())

    def test_request_cancellation_sets_requested_flag(self) -> None:
        adapter = AnalysisCancellationAdapter()
        adapter.bind_new_cancellation_signal()
        adapter.request_cancellation()
        self.assertTrue(adapter.is_cancellation_requested())

    def test_clear_cancellation_signal_resets_state_to_false(self) -> None:
        adapter = AnalysisCancellationAdapter()
        adapter.bind_new_cancellation_signal()
        adapter.request_cancellation()
        adapter.clear_cancellation_signal()
        self.assertFalse(adapter.is_cancellation_requested())

    def test_clear_cancellation_signal_when_unbound_does_not_fail(self) -> None:
        adapter = AnalysisCancellationAdapter()
        adapter.clear_cancellation_signal()
        self.assertFalse(adapter.is_cancellation_requested())

    def test_cancellation_signal_is_shared_across_adapter_instances(self) -> None:
        first_adapter = AnalysisCancellationAdapter()
        second_adapter = AnalysisCancellationAdapter()
        first_adapter.bind_new_cancellation_signal()
        first_adapter.request_cancellation()
        self.assertTrue(second_adapter.is_cancellation_requested())

    def test_cancellation_requested_in_caller_is_visible_to_copied_context_in_thread(
        self,
    ) -> None:
        adapter = AnalysisCancellationAdapter()
        adapter.bind_new_cancellation_signal()

        worker_observed_status: list[bool] = []

        def worker() -> None:
            worker_adapter = AnalysisCancellationAdapter()
            worker_observed_status.append(worker_adapter.is_cancellation_requested())

        context = copy_context()
        adapter.request_cancellation()
        thread = Thread(target=context.run, args=(worker,))
        thread.start()
        thread.join()

        self.assertEqual(worker_observed_status, [True])

    def test_cancellation_requested_by_thread_with_copied_context_is_visible_to_caller(
        self,
    ) -> None:
        adapter = AnalysisCancellationAdapter()
        adapter.bind_new_cancellation_signal()

        def worker() -> None:
            worker_adapter = AnalysisCancellationAdapter()
            worker_adapter.request_cancellation()

        context = copy_context()
        thread = Thread(target=context.run, args=(worker,))
        thread.start()
        thread.join()

        self.assertTrue(adapter.is_cancellation_requested())

    def test_binding_inside_copied_context_does_not_leak_to_caller(self) -> None:
        adapter = AnalysisCancellationAdapter()
        isolated_context = copy_context()
        isolated_context.run(adapter.bind_new_cancellation_signal)
        self.assertFalse(adapter.is_cancellation_requested())
