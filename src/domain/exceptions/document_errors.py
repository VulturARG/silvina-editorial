from src.domain.exceptions.base_src_error import BaseSrcError


class DocumentError(BaseSrcError):
    """Base class for all document-related exceptions."""


class DocumentNotFound(DocumentError):
    """Raised when a document file cannot be located."""

    MESSAGE = "The document file could not be found."

    def __init__(self, detail: str | None = None) -> None:
        """Store the optional detail that pinpoints the missing file."""
        super().__init__()
        self.detail = detail

    def dict(self) -> "dict[str, str]":
        """Return the error message, followed by the detail when one is given."""
        if self.detail is None:
            return super().dict()
        return {"error": f"{self.MESSAGE} {self.detail}"}


class DocumentEmpty(DocumentError):
    """Raised when a document has no readable content."""

    MESSAGE = "The document has no readable content."


class DocumentUnreadable(DocumentError):
    """Raised when a document cannot be read or parsed."""

    MESSAGE = "The document could not be read."


class DocumentInvalidType(DocumentError):
    """Raised when a document has an invalid or unsupported file extension."""

    MESSAGE = "The document type is invalid. Only .docx files are supported."

    def __init__(self, detail: str | None = None) -> None:
        """Store the optional detail that pinpoints the offending file."""
        super().__init__()
        self.detail = detail

    def dict(self) -> "dict[str, str]":
        """Return the error message, followed by the detail when one is given."""
        if self.detail is None:
            return super().dict()
        return {"error": f"{self.MESSAGE} {self.detail}"}


class DocumentTooLarge(DocumentError):
    """Raised when an uploaded document exceeds the maximum allowed size."""

    MESSAGE = "The document file exceeds the maximum allowed size."


class DocumentBodyNotLocated(DocumentError):
    """Raised when the repeated title that opens the article body cannot be found."""

    MESSAGE = "The article body could not be located: the repeated title was not found."


class DocumentBodyTooLong(DocumentError):
    """Raised when the article body exceeds the maximum number of characters allowed."""

    MESSAGE = "No se realizó ningún análisis."

    def __init__(self, body_characters: int, maximum_body_characters: int) -> None:
        """Store the body size and the maximum that the article exceeded."""
        super().__init__()
        self.body_characters = body_characters
        self.maximum_body_characters = maximum_body_characters

    def dict(self) -> "dict[str, str]":
        """Return the Spanish message stating both character counts and that nothing was analyzed."""
        return {
            "error": (
                f"El cuerpo del artículo tiene {self.body_characters} caracteres "
                f"y supera el máximo permitido de {self.maximum_body_characters}. {self.MESSAGE}"
            )
        }
