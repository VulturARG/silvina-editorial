from unittest import TestCase

from src.domain.dtos.article_body_dto import ArticleBodyDTO


class TestArticleBodyDTO(TestCase):
    def test_char_count_joins_title_and_paragraphs_with_single_space(self):
        body = ArticleBodyDTO(
            title="Title",
            abstract_paragraphs=(),
            paragraphs=("First.", "Second."),
        )

        self.assertEqual(body.char_count, len("Title First. Second."))

    def test_char_count_excludes_abstract_paragraphs(self):
        body = ArticleBodyDTO(
            title="Title",
            abstract_paragraphs=("An abstract that must not be counted.",),
            paragraphs=("Body.",),
        )

        self.assertEqual(body.char_count, len("Title Body."))

    def test_char_count_is_title_length_when_there_are_no_body_paragraphs(self):
        body = ArticleBodyDTO(title="Title", abstract_paragraphs=(), paragraphs=())

        self.assertEqual(body.char_count, len("Title"))
