from src.domain.dtos.article_size_thresholds_dto import ArticleSizeThresholdsDTO
from src.domain.enums.article_size import ArticleSize


class ArticleSizeClassifier:
    """Classifies an article's size based on its character count."""

    def __init__(self, *, thresholds: ArticleSizeThresholdsDTO) -> None:
        self._thresholds = thresholds

    def classify(self, char_count: int) -> ArticleSize:
        """Classify article size based on character count with spaces."""
        if self._thresholds.long_min_chars <= char_count <= self._thresholds.long_max_chars:
            return ArticleSize.LONG
        if self._thresholds.long_max_chars < char_count <= self._thresholds.extra_long_max_chars:
            return ArticleSize.EXTRA_LONG
        if self._thresholds.short_min_chars <= char_count <= self._thresholds.short_max_chars:
            return ArticleSize.SHORT
        if (
            self._thresholds.undefined_min_chars
            <= char_count
            <= self._thresholds.undefined_max_chars
        ):
            return ArticleSize.UNDEFINED
        return ArticleSize.OUT_OF_RANGE
