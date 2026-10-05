from src.domain.exceptions.decorators.generic_error_handler import generic_error_handler
from src.domain.language_model.language_model_warmer import LanguageModelWarmer


class WarmUpLanguageModelUseCase:
    """Orchestrates language model warmup to avoid cold start latency."""

    def __init__(self, language_model_warmer: LanguageModelWarmer) -> None:
        self._language_model_warmer = language_model_warmer

    @generic_error_handler
    def execute(self) -> None:
        """Execute the language model warmup."""
        self._language_model_warmer.warm_up()
