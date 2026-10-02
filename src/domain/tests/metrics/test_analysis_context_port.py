from unittest import TestCase

from src.domain.metrics.analysis_context_port import AnalysisContextPort
from src.domain.tests.metrics.fake_analysis_context_port import FakeAnalysisContextPort


class TestAnalysisContextPort(TestCase):
    def test_direct_instantiation_raises_type_error(self) -> None:
        port_class: type = AnalysisContextPort
        with self.assertRaises(TypeError):
            port_class()

    def test_fake_is_instance_of_analysis_context_port(self) -> None:
        fake_port = FakeAnalysisContextPort()
        self.assertIsInstance(fake_port, AnalysisContextPort)

    def test_fake_returns_none_initially(self) -> None:
        fake_port = FakeAnalysisContextPort()
        self.assertIsNone(fake_port.get_analysis_id())

    def test_fake_returns_the_analysis_id_after_set(self) -> None:
        fake_port = FakeAnalysisContextPort()
        fake_port.set_analysis_id("analysis-123")
        self.assertEqual(fake_port.get_analysis_id(), "analysis-123")

    def test_fake_overwrites_previous_analysis_id(self) -> None:
        fake_port = FakeAnalysisContextPort()
        fake_port.set_analysis_id("analysis-123")
        fake_port.set_analysis_id("analysis-456")
        self.assertEqual(fake_port.get_analysis_id(), "analysis-456")

    def test_fake_returns_none_after_clear(self) -> None:
        fake_port = FakeAnalysisContextPort()
        fake_port.set_analysis_id("analysis-123")
        fake_port.clear_analysis_id()
        self.assertIsNone(fake_port.get_analysis_id())

    def test_fake_clear_without_previous_analysis_id_does_not_fail(self) -> None:
        fake_port = FakeAnalysisContextPort()
        fake_port.clear_analysis_id()
        self.assertIsNone(fake_port.get_analysis_id())
