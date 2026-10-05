from src.application.warm_up_language_model_use_case import WarmUpLanguageModelUseCase
from src.domain.enums.ai_provider import AiProvider
from src.domain.language_model.language_model_warmer import LanguageModelWarmer
from src.domain.language_model.language_model_warmup_port import LanguageModelWarmupPort
from src.infrastructure.adapters.llm_generator.noop_language_model_warmup_adapter import (
    NoOpLanguageModelWarmupAdapter,
)
from src.infrastructure.adapters.llm_generator.ollama_backend_error_mapper import (
    OllamaBackendErrorMapper,
)
from src.infrastructure.adapters.llm_generator.ollama_language_model_warmup_adapter import (
    OllamaLanguageModelWarmupAdapter,
)
from src.infrastructure.env_config import EnvConfig


class WarmUpLanguageModelUseCaseWiring:
    """Dependency wiring assembling the language model warmup use case."""

    def get_warm_up_language_model_use_case(self) -> WarmUpLanguageModelUseCase:
        """Return a fully assembled language model warmup use case."""
        return WarmUpLanguageModelUseCase(language_model_warmer=self._language_model_warmer())

    def _language_model_warmer(self) -> LanguageModelWarmer:
        return LanguageModelWarmer(language_model_warmup_port=self._language_model_warmup_port())

    def _language_model_warmup_port(self) -> LanguageModelWarmupPort:
        env_config = self._env_config()
        if env_config.llm_provider is AiProvider.OLLAMA and env_config.ollama_warmup_on_startup:
            return OllamaLanguageModelWarmupAdapter(
                model_name=env_config.ollama_model_name,
                base_url=env_config.ollama_base_url,
                keep_alive=env_config.ollama_model_keep_alive,
                num_ctx=env_config.ollama_num_ctx,
                error_mapper=OllamaBackendErrorMapper(),
            )
        return NoOpLanguageModelWarmupAdapter()

    def _env_config(self) -> EnvConfig:
        return EnvConfig()
