from unittest import TestCase

from src.domain.document.article_length_checker import ArticleLengthChecker
from src.domain.dtos.article_body_dto import ArticleBodyDTO
from src.domain.dtos.article_length_norms_dto import ArticleLengthNormsDTO
from src.domain.dtos.document_content_dto import DocumentContentDTO
from src.domain.exceptions.document_errors import DocumentBodyNotLocated, DocumentBodyTooLong

MAXIMUM_BODY_CHARACTERS = 100
TITLE = "Title"


def _build_content_with_body_characters(body_characters: int) -> DocumentContentDTO:
    paragraph = "x" * (body_characters - len(TITLE) - 1)
    body = ArticleBodyDTO(title=TITLE, abstract_paragraphs=(), paragraphs=(paragraph,))
    return DocumentContentDTO(word_count=0, char_count=body_characters, body=body)


class TestArticleLengthChecker(TestCase):
    def setUp(self):
        self._checker = ArticleLengthChecker(
            article_length_norms=ArticleLengthNormsDTO(max_body_chars=MAXIMUM_BODY_CHARACTERS)
        )

    def test_accepts_body_at_maximum_characters(self):
        self._checker.check(_build_content_with_body_characters(MAXIMUM_BODY_CHARACTERS))

    def test_rejects_body_one_character_above_maximum(self):
        with self.assertRaises(DocumentBodyTooLong):
            self._checker.check(_build_content_with_body_characters(MAXIMUM_BODY_CHARACTERS + 1))

    def test_too_long_error_carries_body_size_and_maximum(self):
        with self.assertRaises(DocumentBodyTooLong) as context:
            self._checker.check(_build_content_with_body_characters(MAXIMUM_BODY_CHARACTERS + 1))

        self.assertEqual(context.exception.body_characters, MAXIMUM_BODY_CHARACTERS + 1)
        self.assertEqual(context.exception.maximum_body_characters, MAXIMUM_BODY_CHARACTERS)

    def test_raises_body_not_located_when_body_is_missing(self):
        content = DocumentContentDTO(word_count=0, char_count=0)

        with self.assertRaises(DocumentBodyNotLocated):
            self._checker.check(content)
