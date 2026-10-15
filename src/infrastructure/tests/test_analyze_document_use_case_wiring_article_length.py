from unittest import TestCase

from src.domain.document.article_length_checker import ArticleLengthChecker
from src.domain.dtos.article_body_dto import ArticleBodyDTO
from src.domain.dtos.document_content_dto import DocumentContentDTO
from src.domain.exceptions.document_errors import DocumentBodyTooLong
from src.infrastructure.editorial_norms_loader import EditorialNormsLoader
from src.infrastructure.resources.project import EDITORIAL_NORMS_FILE_PATH
from src.infrastructure.wirings.analyze_document_use_case_wiring import (
    AnalyzeDocumentUseCaseWiring,
)

TITLE = "Title"


def _build_content_with_body_characters(body_characters: int) -> DocumentContentDTO:
    paragraph = "x" * (body_characters - len(TITLE) - 1)
    body = ArticleBodyDTO(title=TITLE, abstract_paragraphs=(), paragraphs=(paragraph,))
    return DocumentContentDTO(word_count=0, char_count=body_characters, body=body)


class TestAnalyzeDocumentUseCaseWiringArticleLength(TestCase):
    """Verifies the article length checker assembled by AnalyzeDocumentUseCaseWiring."""

    def setUp(self):
        editorial_norms = EditorialNormsLoader(EDITORIAL_NORMS_FILE_PATH).load()
        self._maximum_body_characters = editorial_norms.article_length.max_body_chars

    def test_wiring_builds_article_length_checker(self):
        checker = AnalyzeDocumentUseCaseWiring()._get_article_length_checker()

        self.assertIsInstance(checker, ArticleLengthChecker)

    def test_checker_accepts_body_at_real_editorial_norms_maximum(self):
        checker = AnalyzeDocumentUseCaseWiring()._get_article_length_checker()

        checker.check(_build_content_with_body_characters(self._maximum_body_characters))

    def test_checker_rejects_body_above_real_editorial_norms_maximum(self):
        checker = AnalyzeDocumentUseCaseWiring()._get_article_length_checker()

        with self.assertRaises(DocumentBodyTooLong):
            checker.check(_build_content_with_body_characters(self._maximum_body_characters + 1))
