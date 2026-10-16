class TitleNormalizer:
    """Normalize titles so that they compare regardless of case, colons, periods and spacing."""

    @staticmethod
    def normalize(text: str) -> str:
        """Return the lowercase text with colons and periods turned into spaces and whitespace collapsed."""
        return " ".join(text.lower().replace(":", " ").replace(".", " ").split())
