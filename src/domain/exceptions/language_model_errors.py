from src.domain.exceptions.base_src_error import BaseSrcError


class LanguageModelError(BaseSrcError):
    """Base class for all language model-related exceptions."""


class LanguageModelUnavailable(LanguageModelError):
    """Raised when the language model backend is unavailable."""

    MESSAGE = "The language model backend is unavailable."


class LanguageModelNotFound(LanguageModelError):
    """Raised when the configured language model is not installed in the backend."""

    MESSAGE = "The configured language model is not installed in the backend."


class LanguageModelLoadFailed(LanguageModelError):
    """Raised when the language model cannot be loaded or run by the backend."""

    MESSAGE = (
        "The language model could not be loaded or run by the backend. "
        "Check the available memory and the backend log."
    )
