from unittest import TestCase

from src.domain.classification.article_size_classifier import ArticleSizeClassifier
from src.domain.dtos.article_size_thresholds_dto import ArticleSizeThresholdsDTO
from src.domain.enums.article_size import ArticleSize


class TestArticleSizeClassifier(TestCase):
    def test_each_threshold_boundary_maps_to_correct_article_size(self):
        classifier = ArticleSizeClassifier(
            thresholds=ArticleSizeThresholdsDTO(
                short_min_chars=16000,
                short_max_chars=24000,
                undefined_min_chars=24001,
                undefined_max_chars=35999,
                long_min_chars=36000,
                long_max_chars=40000,
                extra_long_max_chars=40000,
            )
        )

        self.assertEqual(classifier.classify(16000), ArticleSize.SHORT)
        self.assertEqual(classifier.classify(24000), ArticleSize.SHORT)
        self.assertEqual(classifier.classify(24001), ArticleSize.UNDEFINED)
        self.assertEqual(classifier.classify(35999), ArticleSize.UNDEFINED)
        self.assertEqual(classifier.classify(36000), ArticleSize.LONG)
        self.assertEqual(classifier.classify(40000), ArticleSize.LONG)
        self.assertEqual(classifier.classify(40001), ArticleSize.OUT_OF_RANGE)

    def test_custom_thresholds_classify_correctly(self):
        classifier = ArticleSizeClassifier(
            thresholds=ArticleSizeThresholdsDTO(
                short_min_chars=1000,
                short_max_chars=2000,
                undefined_min_chars=2001,
                undefined_max_chars=2999,
                long_min_chars=3000,
                long_max_chars=4000,
                extra_long_max_chars=4000,
            )
        )

        self.assertEqual(classifier.classify(1500), ArticleSize.SHORT)
        self.assertEqual(classifier.classify(2500), ArticleSize.UNDEFINED)
        self.assertEqual(classifier.classify(3500), ArticleSize.LONG)
        self.assertEqual(classifier.classify(16000), ArticleSize.OUT_OF_RANGE)
