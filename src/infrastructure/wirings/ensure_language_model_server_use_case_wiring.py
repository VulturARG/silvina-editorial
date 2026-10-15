from src.application.ensure_language_model_server_use_case import (
    EnsureLanguageModelServerUseCase,
)
from src.infrastructure.wirings.language_model_server_wiring import (
    LanguageModelServerWiring,
)


class EnsureLanguageModelServerUseCaseWiring(LanguageModelServerWiring):
    """Dependency wiring assembling the language model server check and start use case."""

    def get_ensure_language_model_server_use_case(
        self,
    ) -> EnsureLanguageModelServerUseCase:
        """Return a fully assembled ensure language model server use case."""
        return EnsureLanguageModelServerUseCase(
            language_model_server_starter=self._language_model_server_starter()
        )
