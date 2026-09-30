from abc import ABC, abstractmethod

from src.domain.dtos.laya_decision_result_dto import LayaDecisionResultDTO


class LayaDecisionPort(ABC):
    """Port for obtaining all Laya editorial decisions for a document text sample."""

    @abstractmethod
    def decide(self, text_sample: str) -> LayaDecisionResultDTO:
        """Return the Laya decisions for the given text sample."""
