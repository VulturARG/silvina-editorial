from unittest import TestCase

from src.domain.classification.article_size_classifier import ArticleSizeClassifier
from src.domain.dtos.article_size_thresholds_dto import ArticleSizeThresholdsDTO
from src.domain.enums.article_size import ArticleSize


class TestArticleSizeClassifierExtraLong(TestCase):
    def setUp(self) -> None:
        self._classifier = ArticleSizeClassifier(
            thresholds=ArticleSizeThresholdsDTO(
                short_min_chars=16000,
                short_max_chars=24000,
                undefined_min_chars=24001,
                undefined_max_chars=35999,
                long_min_chars=36000,
                long_max_chars=40000,
                extra_long_max_chars=75000,
            )
        )

    def test_long_max_chars_is_still_long(self):
        self.assertEqual(self._classifier.classify(40000), ArticleSize.LONG)

    def test_one_above_long_max_chars_is_extra_long(self):
        self.assertEqual(self._classifier.classify(40001), ArticleSize.EXTRA_LONG)

    def test_extra_long_max_chars_is_extra_long(self):
        self.assertEqual(self._classifier.classify(75000), ArticleSize.EXTRA_LONG)

    def test_one_above_extra_long_max_chars_is_out_of_range(self):
        self.assertEqual(self._classifier.classify(75001), ArticleSize.OUT_OF_RANGE)
