from enum import Enum


class ClassificationConfidence(float, Enum):
    """Confidence levels assigned by ArticleClassifier's SCIENTIFIC rule-table branches."""

    IMRYD_OVERRIDE = 0.95
    FULL_SIGNAL_MATCH = 0.90
    RECENT_BIBLIOGRAPHY_SUPPORT = 0.86
    COMPLETE_BIBLIOGRAPHY_SUPPORT = 0.85
    SUFFICIENT_REFERENCE_COUNT = 0.83

    def __format__(self, format_spec: str) -> str:
        """Format confidence float value using the given format specification."""
        return float.__format__(self.value, format_spec)
