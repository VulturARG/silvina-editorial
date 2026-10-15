from src.domain.language_model.language_model_server_port import (
    LanguageModelServerPort,
)


class NoOpLanguageModelServerAdapter(LanguageModelServerPort):
    """No-operation server adapter used when external providers are configured."""

    def is_running(self) -> bool:
        """Return True because external or disabled server backends do not need local management."""
        return True

    def start(self) -> None:
        """Do nothing because external or disabled server backends do not need local startup."""

    def mark_in_use(self) -> None:
        """Do nothing because external or disabled server backends do not need lease management."""

    def mark_idle(self) -> None:
        """Do nothing because external or disabled server backends do not need lease management."""
