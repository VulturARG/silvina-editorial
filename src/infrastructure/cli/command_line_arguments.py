from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar


@dataclass(frozen=True)
class CommandLineArguments:
    """Values received from the command line, before any default is resolved."""

    CLASSIFICATION_PROMPT_NAME: ClassVar[str] = "s4_s5_s6_signal_prompt"
    PROMPT_NAMES: ClassVar[tuple[str, ...]] = (
        CLASSIFICATION_PROMPT_NAME,
        "alignment_prompt",
        "argumentation_conclusions_prompt",
        "clarity_coherence_prompt",
        "contribution_prompt",
        "research_lines",
    )

    document_name: str | None = None
    input_directory: Path | None = None
    output_directory: Path | None = None
    ollama_model_name: str | None = None
    use_external_llm: bool | None = None
    llm_provider: str | None = None
    external_llm_model_name: str | None = None
    app_mode: str | None = None
    s4_s5_s6_signal_prompt: Path | None = None
    alignment_prompt: Path | None = None
    argumentation_conclusions_prompt: Path | None = None
    clarity_coherence_prompt: Path | None = None
    contribution_prompt: Path | None = None
    research_lines: Path | None = None
    prompts_directory: Path | None = None

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

    def prompt_file_overrides(self) -> dict[str, Path | None]:
        """Return the prompt file overrides keyed by the resource file stem each one replaces."""
        return {
            prompt_name: self._prompt_file_path(prompt_name) for prompt_name in self.PROMPT_NAMES
        }

    def _prompt_file_path(self, prompt_name: str) -> Path | None:
        directory: Path | None = getattr(self, prompt_name)
        return None if directory is None else directory / f"{prompt_name}.txt"

    @classmethod
    def prompt_root_relative_paths(cls) -> tuple[Path, ...]:
        """Return the files a complete prompts root must contain, relative to that root."""
        return tuple(
            cls._prompt_root_relative_path(prompt_name) for prompt_name in cls.PROMPT_NAMES
        )

    @classmethod
    def _prompt_root_relative_path(cls, prompt_name: str) -> Path:
        is_classification_prompt = prompt_name == cls.CLASSIFICATION_PROMPT_NAME
        folder_name = "classification" if is_classification_prompt else "quality"
        return Path(folder_name) / f"{prompt_name}.txt"
