from typing import Any

import ollama

from src.domain.language_model.language_model_warmup_port import LanguageModelWarmupPort
from src.infrastructure.adapters.llm_generator.ollama_backend_error_mapper import (
    OllamaBackendErrorMapper,
)


class OllamaLanguageModelWarmupAdapter(LanguageModelWarmupPort):
    """Warms up a local Ollama language model backend by sending an empty prompt."""

    def __init__(
        self,
        model_name: str,
        base_url: str,
        keep_alive: str,
        num_ctx: int | None,
        error_mapper: OllamaBackendErrorMapper,
    ) -> None:
        self._model_name = model_name
        self._base_url = base_url
        self._keep_alive = keep_alive
        self._num_ctx = num_ctx
        self._error_mapper = error_mapper

    def warm_up(self) -> None:
        """Load the language model into memory with the configured keep-alive duration."""
        generate_kwargs: dict[str, Any] = {
            "model": self._model_name,
            "prompt": "",
            "keep_alive": self._keep_alive,
        }
        if self._num_ctx is not None:
            generate_kwargs["options"] = {"num_ctx": self._num_ctx}
        try:
            client = ollama.Client(host=self._base_url)
            client.generate(**generate_kwargs)
        except (ollama.RequestError, ollama.ResponseError, ConnectionError) as exception:
            mapped_exception = self._error_mapper.map(exception)
            raise mapped_exception from exception
