from enum import Enum


class ArticleType(Enum):
    """Article type classification."""

    SCIENTIFIC = "científico"
    POPULAR_SCIENCE = "divulgación"
    OPINION = "opinión"
    UNKNOWN = "unknown"
