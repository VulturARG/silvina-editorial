class FeedbackTextCleaner:
    """Cleans title headers, dangling asterisks and normalization of feedback text."""

    def clean_title_text(self, raw_text: str) -> str:
        """Strip surrounding whitespace, outer bold markers and trailing colons."""
        cleaned = raw_text.strip()
        if cleaned.endswith(":"):
            cleaned = cleaned[:-1].strip()
        if cleaned.startswith("**") and cleaned.endswith("**"):
            cleaned = cleaned[2:-2].strip()
        if cleaned.endswith(":"):
            cleaned = cleaned[:-1].strip()
        return cleaned

    def clean_dangling_bold(self, text: str) -> str:
        """Remove an unmatched trailing bold marker and normalize whitespace."""
        cleaned = text.strip()
        if cleaned.count("**") % 2 == 1:
            last_index = cleaned.rfind("**")
            cleaned = cleaned[:last_index] + cleaned[last_index + 2 :]
            cleaned = " ".join(cleaned.split())
        return cleaned
