from unittest import TestCase

from src.domain.dtos.article_body_dto import ArticleBodyDTO


class TestArticleBodyDTOText(TestCase):
    def test_text_joins_title_and_body_paragraphs_with_single_space(self):
        body = ArticleBodyDTO(
            title="Title",
            abstract_paragraphs=(),
            paragraphs=("First.", "Second."),
        )

        self.assertEqual(body.text, "Title First. Second.")

    def test_text_excludes_abstract_paragraphs(self):
        body = ArticleBodyDTO(
            title="Title",
            abstract_paragraphs=("An abstract that must not appear.",),
            paragraphs=("Body.",),
        )

        self.assertEqual(body.text, "Title Body.")

    def test_text_is_title_alone_when_there_are_no_body_paragraphs(self):
        body = ArticleBodyDTO(title="Title", abstract_paragraphs=(), paragraphs=())

        self.assertEqual(body.text, "Title")

    def test_char_count_equals_length_of_text(self):
        body = ArticleBodyDTO(
            title="Title",
            abstract_paragraphs=("Abstract.",),
            paragraphs=("First.", "Second."),
        )

        self.assertEqual(body.char_count, len(body.text))
