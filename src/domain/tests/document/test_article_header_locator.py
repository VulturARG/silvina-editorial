from unittest import TestCase

from src.domain.document.article_header_locator import ArticleHeaderLocator
from src.domain.tests.dtos.editorial_norms_builder_for_test import build_editorial_norms_for_test


class TestArticleHeaderLocator(TestCase):
    """Unit tests for ArticleHeaderLocator."""

    def test_returns_paragraph_after_single_line_title(self):
        authors = self._build_locator().locate_authors(
            paragraphs=["Main title", "Jane Doe", "Resumen", "Abstract sentence."],
            repeated_title="Main title",
        )

        self.assertEqual(authors, "Jane Doe")

    def test_returns_paragraph_after_two_line_title(self):
        authors = self._build_locator().locate_authors(
            paragraphs=["Main title:", "Subtitle", "Jane Doe y John Roe", "Resumen"],
            repeated_title="Main title: Subtitle",
        )

        self.assertEqual(authors, "Jane Doe y John Roe")

    def test_returns_none_when_abstract_heading_follows_title(self):
        authors = self._build_locator().locate_authors(
            paragraphs=["Main title", "Resumen", "Abstract sentence."],
            repeated_title="Main title",
        )

        self.assertIsNone(authors)

    def test_returns_none_when_no_leading_paragraph_matches_repeated_title(self):
        authors = self._build_locator().locate_authors(
            paragraphs=["Other title", "Jane Doe", "Resumen"],
            repeated_title="Main title",
        )

        self.assertIsNone(authors)

    def _build_locator(self) -> ArticleHeaderLocator:
        return ArticleHeaderLocator(abstract_norms=build_editorial_norms_for_test().abstract)
