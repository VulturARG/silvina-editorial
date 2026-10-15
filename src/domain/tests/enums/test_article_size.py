from unittest import TestCase

from src.domain.enums.article_size import ArticleSize


class TestArticleSize(TestCase):
    def test_members_and_values(self):
        self.assertEqual(ArticleSize.LONG.value, "largo")
        self.assertEqual(ArticleSize.EXTRA_LONG.value, "extra_largo")
        self.assertEqual(ArticleSize.SHORT.value, "corto")
        self.assertEqual(ArticleSize.UNDEFINED.value, "no_definido")
        self.assertEqual(ArticleSize.OUT_OF_RANGE.value, "fuera_rango")

    def test_member_count(self):
        self.assertEqual(len(ArticleSize), 5)
