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
