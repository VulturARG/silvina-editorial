from src.application.release_language_model_server_use_case import (
    ReleaseLanguageModelServerUseCase,
)
from src.infrastructure.wirings.language_model_server_wiring import (
    LanguageModelServerWiring,
)


class ReleaseLanguageModelServerUseCaseWiring(LanguageModelServerWiring):
    """Dependency wiring assembling the language model server release use case."""

    def get_release_language_model_server_use_case(
        self,
    ) -> ReleaseLanguageModelServerUseCase:
        """Return a fully assembled release language model server use case."""
        return ReleaseLanguageModelServerUseCase(
            language_model_server_starter=self._language_model_server_starter()
        )
