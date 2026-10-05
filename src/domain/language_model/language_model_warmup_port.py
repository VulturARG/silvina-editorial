from abc import ABC, abstractmethod


class LanguageModelWarmupPort(ABC):
    """Port for warming up a language model backend."""

    @abstractmethod
    def warm_up(self) -> None:
        """Load the language model into memory so that the first real request does not pay the load time."""
