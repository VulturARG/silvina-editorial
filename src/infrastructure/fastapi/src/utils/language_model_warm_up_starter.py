"""Background starter for pre-warming the language model on server launch."""

from logging import getLogger
from threading import Thread

from src.application.warm_up_language_model_use_case import (
    WarmUpLanguageModelUseCase,
)
from src.domain.exceptions.base_src_error import BaseSrcError

logger = getLogger(__name__)


class LanguageModelWarmUpStarter:
    """Starts language model warmup in a daemon background thread so the server never waits for it."""

    def __init__(self, warm_up_use_case: WarmUpLanguageModelUseCase) -> None:
        """Initialize the starter with the warm-up use case."""
        self._warm_up_use_case = warm_up_use_case

    def start(self) -> Thread:
        """Create and start a daemon background thread for warmup, returning the started thread."""
        thread = Thread(target=self._run, daemon=True)
        thread.start()
        return thread

    def _run(self) -> None:
        """Execute the warm-up use case and capture exceptions without raising."""
        try:
            self._warm_up_use_case.execute()
        except BaseSrcError as exception:
            logger.warning(
                "Language model warmup failed: %s",
                exception.dict().get("error", str(exception)),
            )
        except Exception as exception:
            logger.warning(
                "Language model warmup failed unexpectedly: %s",
                str(exception),
            )
