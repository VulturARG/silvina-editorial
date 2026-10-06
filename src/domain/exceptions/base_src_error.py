from typing import Any


class BaseSrcError(Exception):
    """Base class for all own exceptions."""

    MESSAGE: str | None = None

    def __init__(self) -> None:
        """Initialize base error with per-instance logging state."""
        super().__init__()
        self.was_error_logged: bool = False

    def dict(self) -> "dict[str, str]":
        """Return error message as dict"""

        default_message = (
            f"The '{self.__class__.__name__}' base class should not be used to raise exceptions."
        )
        message = self.MESSAGE if self.MESSAGE is not None else default_message
        return {"error": message}


class SrcGenericError(BaseSrcError):
    """Wraps unexpected exceptions from infrastructure as a generic domain error."""

    def __init__(
        self,
        exception_or_message: Any,
    ) -> None:
        """Store the human-readable message from the given exception or string."""
        super().__init__()
        self._exception_or_message = str(exception_or_message)

    def dict(self) -> "dict[str, str]":
        """Return the wrapped error message as a dictionary."""
        return {"error": self._exception_or_message}


class SrcBaseWarning(BaseSrcError):
    """Base class for all own warnings."""


class SrcBaseNotAuthorized(BaseSrcError):
    """Base class for all Not Authorized exceptions."""


class SrcBaseNotFound(BaseSrcError):
    """Base class for all Not Found exceptions."""
