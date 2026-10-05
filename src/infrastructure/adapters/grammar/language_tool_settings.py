from dataclasses import dataclass


@dataclass(frozen=True)
class LanguageToolSettings:
    """Runtime configuration limits for the LanguageTool grammar adapter."""

    max_replacements: int
    max_paragraphs: int
    max_chars: int
    max_errors: int
