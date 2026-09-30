"""
Smoke test: ArticleClassifier classifies real sample documents correctly.

Exercises src.domain.classification.article_classifier.ArticleClassifier
against real .docx fixtures. The S4/S5/S6 signals come from a canned Laya
decision (all affirmative) — real .docx parsing and the deterministic signals
(IMRyD override, S2a/S2b/S3) still run.

Run with: python -m pytest tests/smoke/ -v
"""

from pathlib import Path
from unittest import TestCase

from src.domain.dtos.document_content_dto import DocumentContentDTO
from src.domain.dtos.laya_choice_decision_dto import LayaChoiceDecisionDTO
from src.domain.dtos.laya_decision_result_dto import LayaDecisionResultDTO
from src.domain.enums.article_size import ArticleSize
from src.domain.enums.article_type import ArticleType
from src.domain.tests.laya.fake_laya_decision_port import DEFAULT_DECISION_RESULT
from src.infrastructure.adapters.document.docx_text_adapter import DocxTextAdapter
from src.infrastructure.wirings.analyze_document_use_case_wiring import AnalyzeDocumentUseCaseWiring

DOCS = Path(__file__).parent.parent.parent / "docs" / "sample-documents"
_AFFIRMATIVE = LayaChoiceDecisionDTO(answer="SI", probabilities={"SI": 1.0}, confidence=1.0)
_CANNED_LAYA_DECISION = LayaDecisionResultDTO.from_dict(
    {
        **DEFAULT_DECISION_RESULT.as_dict(),
        "s4_research_intent": _AFFIRMATIVE.as_dict(),
        "s5_empirical_evidence": _AFFIRMATIVE.as_dict(),
        "s6_theoretical_framework": _AFFIRMATIVE.as_dict(),
    }
)
_DOCUMENTS = ["1. test_Científico.docx", "2. test_divulgacion_v2.docx", "3. test_opinion_v2.docx"]


class TestClassifyArticleParity(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reader = DocxTextAdapter()
        cls.article_classifier = AnalyzeDocumentUseCaseWiring()._get_article_classifier()

    def _run(self, filename: str):
        paragraphs = self.reader.read_paragraphs(path=str(DOCS / filename))
        document_content = DocumentContentDTO(
            word_count=sum(len(paragraph.split()) for paragraph in paragraphs),
            char_count=sum(len(paragraph) for paragraph in paragraphs),
            paragraphs=paragraphs,
        )
        return self.article_classifier.classify(
            document_content=document_content, laya_decision=_CANNED_LAYA_DECISION
        )

    def test_cientifico_classified_as_popular_science(self):
        self._assert_classifies_as(
            _DOCUMENTS[0], ArticleType.POPULAR_SCIENCE, ArticleSize.UNDEFINED
        )

    def test_divulgacion_classified_as_popular_science(self):
        self._assert_classifies_as(
            _DOCUMENTS[1], ArticleType.POPULAR_SCIENCE, ArticleSize.OUT_OF_RANGE
        )

    def test_opinion_classified_as_popular_science(self):
        self._assert_classifies_as(
            _DOCUMENTS[2], ArticleType.POPULAR_SCIENCE, ArticleSize.OUT_OF_RANGE
        )

    def _assert_classifies_as(
        self, filename: str, expected_type: ArticleType, expected_size: ArticleSize
    ):
        result = self._run(filename)
        self.assertEqual(result.article_type, expected_type)
        self.assertEqual(result.article_size, expected_size)


if __name__ == "__main__":
    import unittest

    unittest.main()
