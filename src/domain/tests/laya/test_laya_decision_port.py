from unittest import TestCase

from src.domain.laya.laya_decision_port import LayaDecisionPort
from src.domain.tests.dtos.test_laya_decision_result_dto import build_decision_result
from src.domain.tests.laya.fake_laya_decision_port import (
    DEFAULT_DECISION_RESULT,
    FakeLayaDecisionPort,
)


class TestLayaDecisionPort(TestCase):
    def test_direct_instantiation_raises_type_error(self):
        with self.assertRaises(TypeError):
            LayaDecisionPort()  # type: ignore[abstract]

    def test_fake_is_instance_of_port(self):
        self.assertIsInstance(FakeLayaDecisionPort(), LayaDecisionPort)

    def test_fake_decide_returns_configured_result(self):
        expected = build_decision_result()
        fake = FakeLayaDecisionPort(result=expected)
        self.assertEqual(fake.decide(text_sample="Sample text"), expected)

    def test_fake_decide_returns_default_result_when_unconfigured(self):
        fake = FakeLayaDecisionPort()
        self.assertEqual(fake.decide(text_sample="Sample text"), DEFAULT_DECISION_RESULT)

    def test_fake_records_received_text_sample(self):
        fake = FakeLayaDecisionPort()
        fake.decide(text_sample="Sample text")
        self.assertEqual(fake.received_text_samples, ["Sample text"])

    def test_fake_raises_configured_error(self):
        fake = FakeLayaDecisionPort(error=ValueError("Decision error"))
        with self.assertRaises(ValueError):
            fake.decide(text_sample="Sample text")
