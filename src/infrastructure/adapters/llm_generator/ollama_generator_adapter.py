import ollama

from src.domain.dtos.llm_generation_dto import LlmGenerationDTO
from src.domain.ports.llm_generator_port import LlmGeneratorPort
from src.infrastructure.adapters.llm_generator.ollama_backend_error_mapper import (
    OllamaBackendErrorMapper,
)


class OllamaGeneratorAdapter(LlmGeneratorPort):
    """Generates text via a local Ollama backend.

    Reasoning mode is configurable; enabling it can consume the token budget and leave the response
    empty.
    """

    def __init__(
        self,
        model_name: str,
        base_url: str,
        think: bool,
        keep_alive: str,
        num_ctx: int | None,
        error_mapper: OllamaBackendErrorMapper,
    ) -> None:
        self._model_name = model_name
        self._base_url = base_url
        self._think = think
        self._keep_alive = keep_alive
        self._num_ctx = num_ctx
        self._error_mapper = error_mapper

    def generate(self, prompt: str, options: dict | None = None) -> str:
        """Return Ollama's generated text for the given prompt."""
        return self.generate_with_usage(prompt=prompt, options=options).text

    def generate_with_usage(self, prompt: str, options: dict | None = None) -> LlmGenerationDTO:
        """Return Ollama's generated text and usage metadata for the given prompt."""
        request_options = (
            {**(options or {}), "num_ctx": self._num_ctx} if self._num_ctx is not None else options
        )
        try:
            client = ollama.Client(host=self._base_url)
            response = client.generate(
                model=self._model_name,
                prompt=prompt,
                options=request_options,
                think=self._think,
                keep_alive=self._keep_alive,
            )
        except (ollama.RequestError, ollama.ResponseError, ConnectionError) as exc:
            mapped_exception = self._error_mapper.map(exc)
            raise mapped_exception from exc
        return LlmGenerationDTO(
            text=response.get("response", "").strip(),
            prompt_tokens=response.get("prompt_eval_count"),
            completion_tokens=response.get("eval_count"),
            done_reason=response.get("done_reason"),
        )
