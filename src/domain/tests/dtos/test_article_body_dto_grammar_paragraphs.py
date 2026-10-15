from unittest import TestCase

from src.domain.dtos.article_body_dto import ArticleBodyDTO


class TestArticleBodyDTOAbstractAndBodyParagraphs(TestCase):
    def test_lists_abstract_then_title_then_body_paragraphs_in_document_order(self):
        body = ArticleBodyDTO(
            title="Title",
            abstract_paragraphs=("Abstract one.", "Abstract two."),
            paragraphs=("First.", "Second."),
        )

        self.assertEqual(
            body.abstract_and_body_paragraphs,
            ["Abstract one.", "Abstract two.", "Title", "First.", "Second."],
        )

    def test_returns_title_alone_when_there_are_no_abstract_and_no_body_paragraphs(self):
        body = ArticleBodyDTO(title="Title", abstract_paragraphs=(), paragraphs=())

        self.assertEqual(body.abstract_and_body_paragraphs, ["Title"])

    def test_returns_a_list_and_not_a_tuple(self):
        body = ArticleBodyDTO(title="Title", abstract_paragraphs=(), paragraphs=("Body.",))

        self.assertIsInstance(body.abstract_and_body_paragraphs, list)
