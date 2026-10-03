from re import Pattern, compile

from markupsafe import Markup, escape


class InlineBoldRenderer:
    """Render inline Markdown bold syntax into safe HTML markup."""

    _BOLD_PATTERN: Pattern[str] = compile(r"\*\*([^\r\n]+?)\*\*")

    def render(self, text: str | None) -> Markup:
        """Escape text and convert paired Markdown bold markers into HTML strong tags."""
        if not text:
            return Markup("")
        escaped_text = str(escape(text))
        rendered_text = self._BOLD_PATTERN.sub(r"<strong>\1</strong>", escaped_text)
        return Markup(rendered_text)

    def __call__(self, text: str | None) -> Markup:
        """Render inline markdown bold syntax into safe HTML markup."""
        return self.render(text)
