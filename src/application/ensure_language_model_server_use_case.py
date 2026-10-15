from src.domain.exceptions.decorators.generic_error_handler import (
    generic_error_handler,
)
from src.domain.language_model.language_model_server_starter import (
    LanguageModelServerStarter,
)


class EnsureLanguageModelServerUseCase:
    """Orchestrates verifying and starting the language model server."""

    def __init__(self, language_model_server_starter: LanguageModelServerStarter) -> None:
        self._language_model_server_starter = language_model_server_starter

    @generic_error_handler
    def execute(self) -> None:
        """Ensure the language model server is running and reachable."""
        self._language_model_server_starter.ensure_running()
