from logging import getLogger
from time import perf_counter

from src.domain.language_model.language_model_server_port import LanguageModelServerPort

logger = getLogger(__name__)

_SERVER_START_LOG_FORMAT = "Language model server started in %.2f seconds"
_SERVER_STARTING_LOG_MESSAGE = "Language model server is not running; starting server..."


class LanguageModelServerStarter:
    """Domain service that ensures the language model server is running before requests."""

    def __init__(self, language_model_server_port: LanguageModelServerPort) -> None:
        self._language_model_server_port = language_model_server_port

    def ensure_running(self) -> None:
        """Start the language model server when it is not already reachable and mark it in use."""
        if self._language_model_server_port.is_running():
            self._language_model_server_port.mark_in_use()
            return
        logger.info(_SERVER_STARTING_LOG_MESSAGE)
        start_time = perf_counter()
        self._language_model_server_port.start()
        duration_seconds = perf_counter() - start_time
        logger.info(_SERVER_START_LOG_FORMAT, duration_seconds)
        self._language_model_server_port.mark_in_use()

    def release(self) -> None:
        """Mark the language model server as idle."""
        self._language_model_server_port.mark_idle()
