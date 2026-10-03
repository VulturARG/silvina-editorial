from importlib import import_module

from src.domain.enums.ai_provider import AiProvider
from src.domain.exceptions.language_model_errors import LanguageModelBackendNotInstalled
from src.domain.ports.llm_generator_port import LlmGeneratorPort

_DEFAULT_REGISTRY: dict[AiProvider, tuple[str, str]] = {
    AiProvider.CLAUDE: (
        "src.infrastructure.adapters.llm_generator.claude_generator_adapter",
        "ClaudeGeneratorAdapter",
    ),
}


class ExternalLlmGeneratorLoader:
    """Loads external language model generator adapters dynamically."""

    def __init__(
        self,
        registry: dict[AiProvider, tuple[str, str]] | None = None,
    ) -> None:
        self._registry = _DEFAULT_REGISTRY if registry is None else registry

    def load(
        self,
        provider: AiProvider,
        model_name: str,
        think: bool,
    ) -> LlmGeneratorPort:
        """Instantiate and return an external language model generator adapter."""
        if provider not in self._registry:
            raise ValueError(
                f"No external language model adapter registered for provider '{provider.value}'"
            )

        module_path, class_name = self._registry[provider]
        try:
            module = import_module(module_path)
        except ModuleNotFoundError as exception:
            raise LanguageModelBackendNotInstalled() from exception

        adapter_class = getattr(module, class_name)
        generator_instance: LlmGeneratorPort = adapter_class(
            model_name=model_name,
            think=think,
        )
        return generator_instance
