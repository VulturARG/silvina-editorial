from unittest import TestCase

from src.domain.laya.laya_decision_maker import LayaDecisionMaker
from src.domain.tests.dtos.test_laya_decision_result_dto import build_decision_result
from src.domain.tests.laya.fake_laya_decision_port import FakeLayaDecisionPort
from src.domain.tests.laya.test_laya_text_sampler import (
    build_document_content,
    build_long_paragraphs,
    build_sampler,
)


class TestLayaDecisionMaker(TestCase):
    def test_decide_sends_the_sampled_state_to_the_port_once(self):
        document_content = build_document_content(build_long_paragraphs())
        text_sampler = build_sampler()
        laya_decision_port = FakeLayaDecisionPort()
        decision_maker = LayaDecisionMaker(
            text_sampler=text_sampler, laya_decision_port=laya_decision_port
        )

        decision_maker.decide(document_content=document_content)

        self.assertEqual(
            laya_decision_port.received_text_samples,
            [text_sampler.build_sample(document_content)],
        )

    def test_decide_returns_the_port_decision_result(self):
        expected = build_decision_result()
        decision_maker = LayaDecisionMaker(
            text_sampler=build_sampler(),
            laya_decision_port=FakeLayaDecisionPort(result=expected),
        )

        result = decision_maker.decide(
            document_content=build_document_content(build_long_paragraphs())
        )

        self.assertEqual(result, expected)

    def test_decide_propagates_port_errors(self):
        decision_maker = LayaDecisionMaker(
            text_sampler=build_sampler(),
            laya_decision_port=FakeLayaDecisionPort(error=ValueError("Laya failure")),
        )

        with self.assertRaises(ValueError):
            decision_maker.decide(document_content=build_document_content(build_long_paragraphs()))
