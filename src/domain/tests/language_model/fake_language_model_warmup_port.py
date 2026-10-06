from src.domain.language_model.language_model_warmup_port import LanguageModelWarmupPort


class FakeLanguageModelWarmupPort(LanguageModelWarmupPort):
    """Fake language model warmup port for testing."""

    def __init__(self, raise_error: Exception | None = None) -> None:
        self._raise_error = raise_error
        self.warm_up_call_count = 0

    def warm_up(self) -> None:
        """Record the call and optionally raise a configured error."""
        self.warm_up_call_count += 1
        if self._raise_error is not None:
            raise self._raise_error
