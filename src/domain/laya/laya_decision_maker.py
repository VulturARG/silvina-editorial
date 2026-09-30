from src.domain.dtos.document_content_dto import DocumentContentDTO
from src.domain.dtos.laya_decision_result_dto import LayaDecisionResultDTO
from src.domain.laya.laya_decision_port import LayaDecisionPort
from src.domain.laya.laya_text_sampler import LayaTextSampler


class LayaDecisionMaker:
    """Obtains all Laya editorial decisions for a document with a single prediction."""

    def __init__(self, text_sampler: LayaTextSampler, laya_decision_port: LayaDecisionPort) -> None:
        self._text_sampler = text_sampler
        self._laya_decision_port = laya_decision_port

    def decide(self, document_content: DocumentContentDTO) -> LayaDecisionResultDTO:
        """Build the Laya state from the document once and return its decisions."""
        text_sample = self._text_sampler.build_sample(document_content=document_content)
        return self._laya_decision_port.decide(text_sample=text_sample)
