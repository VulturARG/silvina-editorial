from logging import getLogger
from time import perf_counter

from src.domain.language_model.language_model_warmup_port import LanguageModelWarmupPort

logger = getLogger(__name__)

_WARMUP_SUCCESS_LOG_FORMAT = "Language model warm-up completed in %.2f seconds"


class LanguageModelWarmer:
    """Domain service that coordinates warming up the language model and logs its duration."""

    def __init__(self, language_model_warmup_port: LanguageModelWarmupPort) -> None:
        self._language_model_warmup_port = language_model_warmup_port

    def warm_up(self) -> None:
        """Warm up the language model and log the elapsed duration in seconds upon success."""
        start_time = perf_counter()
        self._language_model_warmup_port.warm_up()
        duration_seconds = perf_counter() - start_time
        logger.info(_WARMUP_SUCCESS_LOG_FORMAT, duration_seconds)
