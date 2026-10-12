from src.domain.exceptions.base_src_error import BaseSrcError


class EditorialNormsError(BaseSrcError):
    """Base class for all editorial norms-related exceptions."""


class EditorialNormsFileNotFound(EditorialNormsError):
    """Raised when the editorial norms file cannot be located."""

    MESSAGE = "The editorial norms file could not be found."

    def __init__(self, detail: str) -> None:
        """Store the detail that pinpoints the offending file."""
        super().__init__()
        self.detail = detail

    def dict(self) -> dict[str, str]:
        """Return the error message followed by its detail."""
        return {"error": f"{self.MESSAGE} {self.detail}"}


class EditorialNormsFileInvalid(EditorialNormsError):
    """Raised when the editorial norms file is not valid TOML."""

    MESSAGE = "The editorial norms file is not valid TOML."

    def __init__(self, detail: str) -> None:
        """Store the detail that pinpoints the offending file."""
        super().__init__()
        self.detail = detail

    def dict(self) -> dict[str, str]:
        """Return the error message followed by its detail."""
        return {"error": f"{self.MESSAGE} {self.detail}"}


class EditorialNormMissing(EditorialNormsError):
    """Raised when a required editorial norm is absent from the file."""

    MESSAGE = "A required editorial norm is missing."

    def __init__(self, detail: str) -> None:
        """Store the detail that pinpoints the offending section or key."""
        super().__init__()
        self.detail = detail

    def dict(self) -> dict[str, str]:
        """Return the error message followed by its detail."""
        return {"error": f"{self.MESSAGE} {self.detail}"}


class EditorialNormInvalid(EditorialNormsError):
    """Raised when an editorial norm has an invalid type or value."""

    MESSAGE = "An editorial norm has an invalid value."

    def __init__(self, detail: str) -> None:
        """Store the detail that pinpoints the offending section or key."""
        super().__init__()
        self.detail = detail

    def dict(self) -> dict[str, str]:
        """Return the error message followed by its detail."""
        return {"error": f"{self.MESSAGE} {self.detail}"}
