from re import Pattern, compile

from markupsafe import Markup, escape


class InlineBoldRenderer:
    """Render inline Markdown bold and italic syntax into safe HTML markup."""

    _BOLD_PATTERN: Pattern[str] = compile(r"\*\*([^\r\n]+?)\*\*(?!\*)")
    _ITALIC_PATTERN: Pattern[str] = compile(r"(?<!\*)\*(?!\s|\*)([^\r\n*]+?)(?<!\s)\*(?!\*)")

    def render(self, text: str | None) -> Markup:
        """Escape text and convert Markdown bold and italic markers into HTML tags."""
        if not text:
            return Markup("")
        escaped_text = str(escape(text))
        bold_rendered = self._BOLD_PATTERN.sub(r"<strong>\1</strong>", escaped_text)
        italic_rendered = self._ITALIC_PATTERN.sub(r"<em>\1</em>", bold_rendered)
        return Markup(italic_rendered)

    def __call__(self, text: str | None) -> Markup:
        """Render inline markdown bold and italic syntax into safe HTML markup."""
        return self.render(text)
