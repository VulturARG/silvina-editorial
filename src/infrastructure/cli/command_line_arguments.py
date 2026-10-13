from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CommandLineArguments:
    """Values received from the command line, before any default is resolved."""

    document_name: str | None = None
    input_directory: Path | None = None
    output_directory: Path | None = None
    ollama_model_name: str | None = None
    use_external_llm: bool | None = None
    llm_provider: str | None = None
    external_llm_model_name: str | None = None
    app_mode: str | None = None

    def environment_overrides(self) -> dict[str, str | None]:
        """Return the overrides keyed by the environment variable each one replaces."""
        use_external_llm_text = (
            None if self.use_external_llm is None else str(self.use_external_llm).lower()
        )
        return {
            "OLLAMA_MODEL_NAME": self.ollama_model_name,
            "USE_EXTERNAL_LLM": use_external_llm_text,
            "LLM_PROVIDER": self.llm_provider,
            "EXTERNAL_LLM_MODEL_NAME": self.external_llm_model_name,
            "APP_MODE": self.app_mode,
        }
