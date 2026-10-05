from http import HTTPStatus

from ollama import ResponseError

from src.domain.exceptions.language_model_errors import (
    LanguageModelError,
    LanguageModelLoadFailed,
    LanguageModelNotFound,
    LanguageModelUnavailable,
)


class OllamaBackendErrorMapper:
    """Maps Ollama backend exceptions to domain language model errors."""

    def map(self, exception: Exception) -> LanguageModelError:
        """Map a backend exception to a domain language model error."""
        if isinstance(exception, ResponseError):
            if exception.status_code == HTTPStatus.NOT_FOUND:
                return LanguageModelNotFound()
            if (
                isinstance(exception.status_code, int)
                and exception.status_code >= HTTPStatus.INTERNAL_SERVER_ERROR
            ):
                return LanguageModelLoadFailed()
        return LanguageModelUnavailable()
