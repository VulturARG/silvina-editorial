from http import HTTPStatus

import ollama

from src.domain.dtos.llm_generation_dto import LlmGenerationDTO
from src.domain.exceptions.language_model_errors import (
    LanguageModelError,
    LanguageModelLoadFailed,
    LanguageModelNotFound,
    LanguageModelUnavailable,
)
from src.domain.ports.llm_generator_port import LlmGeneratorPort


class OllamaGeneratorAdapter(LlmGeneratorPort):
    """Generates text via a local Ollama backend.

    Reasoning mode is configurable; enabling it can consume the token budget and leave the response
    empty.
    """

    def __init__(self, model_name: str, base_url: str, think: bool) -> None:
        self._model_name = model_name
        self._base_url = base_url
        self._think = think

    def generate(self, prompt: str, options: dict | None = None) -> str:
        """Return Ollama's generated text for the given prompt."""
        return self.generate_with_usage(prompt=prompt, options=options).text

    def generate_with_usage(self, prompt: str, options: dict | None = None) -> LlmGenerationDTO:
        """Return Ollama's generated text and usage metadata for the given prompt."""
        try:
            client = ollama.Client(host=self._base_url)
            response = client.generate(
                model=self._model_name,
                prompt=prompt,
                options=options,
                think=self._think,
            )
        except (ollama.RequestError, ollama.ResponseError, ConnectionError) as exc:
            mapped_exception = self._map_backend_exception(exc)
            raise mapped_exception from exc
        return LlmGenerationDTO(
            text=response.get("response", "").strip(),
            prompt_tokens=response.get("prompt_eval_count"),
            completion_tokens=response.get("eval_count"),
            done_reason=response.get("done_reason"),
        )

    def _map_backend_exception(
        self,
        exception: ollama.RequestError | ollama.ResponseError | ConnectionError,
    ) -> LanguageModelError:
        """Map backend exceptions to domain language model errors."""
        if isinstance(exception, ollama.ResponseError):
            if exception.status_code == HTTPStatus.NOT_FOUND:
                return LanguageModelNotFound()
            if (
                isinstance(exception.status_code, int)
                and exception.status_code >= HTTPStatus.INTERNAL_SERVER_ERROR
            ):
                return LanguageModelLoadFailed()
        return LanguageModelUnavailable()
