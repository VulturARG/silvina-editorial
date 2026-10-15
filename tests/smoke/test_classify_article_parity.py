"""
Smoke test: ArticleClassifier classifies real sample documents correctly.

Exercises src.domain.classification.article_classifier.ArticleClassifier
(wired with src.infrastructure.adapters.llm_generator.ollama_generator_adapter.
OllamaGeneratorAdapter) against real .docx fixtures. Only the S4/S5/S6
signal-extraction network call is mocked with a canned response — real .docx
parsing and the deterministic signals (IMRyD override, S2a/S2b/S3) still run.

Run with: python -m pytest tests/smoke/ -v
"""

from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from src.domain.dtos.document_content_dto import DocumentContentDTO
from src.domain.enums.article_size import ArticleSize
from src.domain.enums.article_type import ArticleType
from src.infrastructure.adapters.document.docx_text_adapter import DocxTextAdapter
from src.infrastructure.wirings.analyze_document_use_case_wiring import AnalyzeDocumentUseCaseWiring

DOCS = Path(__file__).parent.parent.parent / "docs" / "sample-documents"
_CANNED_RESPONSE = {"response": "S4: SI\nS5: SI\nS6: SI"}
_DOCUMENTS = ["1. test_Científico.docx", "2. test_divulgacion_v2.docx", "3. test_opinion_v2.docx"]


class TestClassifyArticleParity(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reader = DocxTextAdapter()
        wiring = AnalyzeDocumentUseCaseWiring()
        cls.article_classifier = wiring._get_article_classifier()
        cls.article_body_locator = wiring._get_article_body_locator()

    def _run(self, filename: str):
        paragraphs = self.reader.read_paragraphs(path=str(DOCS / filename))
        clean_paragraphs = [paragraph.strip() for paragraph in paragraphs if paragraph.strip()]
        document_content = DocumentContentDTO(
            word_count=sum(len(paragraph.split()) for paragraph in paragraphs),
            char_count=sum(len(paragraph) for paragraph in paragraphs),
            paragraphs=paragraphs,
            body=self.article_body_locator.locate(paragraphs=clean_paragraphs),
        )
        with patch(
            "src.infrastructure.adapters.llm_generator.ollama_generator_adapter."
            "ollama.Client.generate",
            return_value=_CANNED_RESPONSE,
        ) as generate:
            result = self.article_classifier.classify(document_content=document_content)
        return result, generate

    def test_cientifico_classified_as_popular_science(self):
        self._assert_classifies_as(_DOCUMENTS[0], ArticleType.POPULAR_SCIENCE, ArticleSize.SHORT)

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
        result, generate = self._run(filename)
        self.assertEqual(result.article_type, expected_type)
        self.assertEqual(result.article_size, expected_size)
        self.assertEqual(generate.call_count, 1)


if __name__ == "__main__":
    import unittest

    unittest.main()
