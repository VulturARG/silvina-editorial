from src.domain.language_model.language_model_server_port import LanguageModelServerPort


class FakeLanguageModelServerPort(LanguageModelServerPort):
    """Fake language model server port for testing."""

    def __init__(
        self,
        is_running_result: bool = True,
        raise_error_on_start: Exception | None = None,
        raise_error_on_mark_idle: Exception | None = None,
        raise_error_on_mark_in_use: Exception | None = None,
    ) -> None:
        self.is_running_result = is_running_result
        self.raise_error_on_start = raise_error_on_start
        self.raise_error_on_mark_idle = raise_error_on_mark_idle
        self.raise_error_on_mark_in_use = raise_error_on_mark_in_use
        self.is_running_call_count = 0
        self.start_call_count = 0
        self.mark_in_use_call_count = 0
        self.mark_idle_call_count = 0

    def is_running(self) -> bool:
        """Record the call and return the configured status."""
        self.is_running_call_count += 1
        return self.is_running_result

    def start(self) -> None:
        """Record the call and optionally raise a configured error."""
        self.start_call_count += 1
        if self.raise_error_on_start is not None:
            raise self.raise_error_on_start

    def mark_in_use(self) -> None:
        """Record the call to mark the server in use."""
        self.mark_in_use_call_count += 1
        if self.raise_error_on_mark_in_use is not None:
            raise self.raise_error_on_mark_in_use

    def mark_idle(self) -> None:
        """Record the call to mark the server idle."""
        self.mark_idle_call_count += 1
        if self.raise_error_on_mark_idle is not None:
            raise self.raise_error_on_mark_idle
