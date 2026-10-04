class FeedbackListMarker:
    """Provides constants and formatting for list item markers."""

    BULLET = "•"

    @classmethod
    def format_numbered(cls, number_string: str) -> str:
        """Format a numeric string into a standard numbered list marker."""
        return f"{number_string}."
