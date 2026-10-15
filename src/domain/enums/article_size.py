from enum import Enum


class ArticleSize(Enum):
    """Article size classification based on character count."""

    LONG = "largo"  # 36,000 - 40,000 chars
    EXTRA_LONG = "extra_largo"
    SHORT = "corto"  # 16,000 - 24,000 chars
    UNDEFINED = "no_definido"  # 24,001 - 35,999 chars
    OUT_OF_RANGE = "fuera_rango"  # Outside all ranges
