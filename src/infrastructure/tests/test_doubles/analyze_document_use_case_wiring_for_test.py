from src.domain.laya.laya_decision_port import LayaDecisionPort
from src.domain.tests.laya.fake_laya_decision_port import FakeLayaDecisionPort
from src.infrastructure.wirings.analyze_document_use_case_wiring import (
    AnalyzeDocumentUseCaseWiring,
)


class AnalyzeDocumentUseCaseWiringForTest(AnalyzeDocumentUseCaseWiring):
    """Production wiring with the Laya checkpoint replaced by an in-memory decision port."""

    def _get_laya_decision_port(self) -> LayaDecisionPort:
        return FakeLayaDecisionPort()
