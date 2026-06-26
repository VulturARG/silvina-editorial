from enum import Enum


class ExtractionFallback(str, Enum):
    """Fallback display values used when document content fields are absent."""

    UNKNOWN_AUTHOR = "Autor no identificado"
