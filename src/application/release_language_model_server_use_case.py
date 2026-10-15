from src.domain.exceptions.decorators.generic_error_handler import (
    generic_error_handler,
)
from src.domain.language_model.language_model_server_starter import (
    LanguageModelServerStarter,
)


class ReleaseLanguageModelServerUseCase:
    """Orchestrates releasing the active hold on the language model server."""

    def __init__(self, language_model_server_starter: LanguageModelServerStarter) -> None:
        self._language_model_server_starter = language_model_server_starter

    @generic_error_handler
    def execute(self) -> None:
        """Mark the language model server as idle."""
        self._language_model_server_starter.release()
