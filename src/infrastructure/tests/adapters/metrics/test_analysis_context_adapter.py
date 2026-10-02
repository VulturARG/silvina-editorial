from contextvars import copy_context
from unittest import TestCase

from src.domain.metrics.analysis_context_port import AnalysisContextPort
from src.infrastructure.adapters.metrics.analysis_context_adapter import AnalysisContextAdapter


class TestAnalysisContextAdapter(TestCase):
    def setUp(self) -> None:
        adapter = AnalysisContextAdapter()
        adapter.clear_analysis_id()

    def tearDown(self) -> None:
        adapter = AnalysisContextAdapter()
        adapter.clear_analysis_id()

    def test_is_instance_of_analysis_context_port(self) -> None:
        adapter = AnalysisContextAdapter()
        self.assertIsInstance(adapter, AnalysisContextPort)

    def test_returns_none_when_nothing_was_set(self) -> None:
        adapter = AnalysisContextAdapter()
        self.assertIsNone(adapter.get_analysis_id())

    def test_returns_the_analysis_id_that_was_set(self) -> None:
        adapter = AnalysisContextAdapter()
        adapter.set_analysis_id("analysis-123")
        self.assertEqual(adapter.get_analysis_id(), "analysis-123")

    def test_overwrites_previous_analysis_id(self) -> None:
        adapter = AnalysisContextAdapter()
        adapter.set_analysis_id("analysis-123")
        adapter.set_analysis_id("analysis-456")
        self.assertEqual(adapter.get_analysis_id(), "analysis-456")

    def test_returns_none_after_clear(self) -> None:
        adapter = AnalysisContextAdapter()
        adapter.set_analysis_id("analysis-123")
        adapter.clear_analysis_id()
        self.assertIsNone(adapter.get_analysis_id())

    def test_clear_without_previous_analysis_id_does_not_fail(self) -> None:
        adapter = AnalysisContextAdapter()
        adapter.clear_analysis_id()
        self.assertIsNone(adapter.get_analysis_id())

    def test_analysis_id_set_through_one_instance_is_visible_from_another_instance(self) -> None:
        first_adapter = AnalysisContextAdapter()
        second_adapter = AnalysisContextAdapter()
        first_adapter.set_analysis_id("analysis-shared")
        self.assertEqual(second_adapter.get_analysis_id(), "analysis-shared")

    def test_analysis_id_set_inside_copied_context_does_not_leak_to_caller(self) -> None:
        adapter = AnalysisContextAdapter()
        isolated_context = copy_context()
        isolated_context.run(adapter.set_analysis_id, "isolated-analysis")
        self.assertIsNone(adapter.get_analysis_id())

    def test_copied_context_inherits_callers_analysis_id(self) -> None:
        adapter = AnalysisContextAdapter()
        adapter.set_analysis_id("analysis-123")
        inherited_analysis_id = copy_context().run(adapter.get_analysis_id)
        self.assertEqual(inherited_analysis_id, "analysis-123")
