from unittest import TestCase

from src.domain.enums.article_type import ArticleType


class TestArticleType(TestCase):
    def test_members_and_values(self):
        self.assertEqual(ArticleType.SCIENTIFIC.value, "científico")
        self.assertEqual(ArticleType.POPULAR_SCIENCE.value, "divulgación")
        self.assertEqual(ArticleType.OPINION.value, "opinión")
        self.assertEqual(ArticleType.UNKNOWN.value, "unknown")

    def test_importable_independently(self):
        self.assertIsNotNone(ArticleType)

    def test_member_count(self):
        self.assertEqual(len(ArticleType), 4)
