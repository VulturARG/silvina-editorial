from abc import ABC, abstractmethod


class LanguageModelServerPort(ABC):
    """Port for checking and starting a language model server backend."""

    @abstractmethod
    def is_running(self) -> bool:
        """Return whether the language model server is running and reachable."""

    @abstractmethod
    def start(self) -> None:
        """Start the language model server and block until it becomes reachable."""

    @abstractmethod
    def mark_in_use(self) -> None:
        """Mark the language model server as actively in use by a process."""

    @abstractmethod
    def mark_idle(self) -> None:
        """Mark the language model server as no longer actively in use."""
