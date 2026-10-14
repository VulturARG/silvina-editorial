class WindowsFileNameSanitizer:
    """Replace the characters that Windows forbids in file names with underscores."""

    REPLACEMENT_CHARACTER = "_"
    INVALID_CHARACTERS = frozenset('<>:"/\\|?*')

    def sanitize(self, text: str) -> str:
        """Return the text with every forbidden file name character replaced."""
        return "".join(
            self.REPLACEMENT_CHARACTER if character in self.INVALID_CHARACTERS else character
            for character in text
        )
