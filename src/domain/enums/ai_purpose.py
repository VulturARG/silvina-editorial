from enum import Enum


class AiPurpose(Enum):
    """Editorial purpose for an external AI interaction."""

    ARTICLE_CLASSIFICATION = "article_classification"
    QUALITY_ANALYSIS = "quality_analysis"
    EDITORIAL_SUITABILITY = "editorial_suitability"
