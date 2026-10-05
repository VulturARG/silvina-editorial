from src.domain.language_model.language_model_warmup_port import LanguageModelWarmupPort


class NoOpLanguageModelWarmupAdapter(LanguageModelWarmupPort):
    """No-operation warmup adapter used when the language model is not a local Ollama model or warmup is disabled."""

    def warm_up(self) -> None:
        """Do nothing because language model warmup is disabled or unneeded."""
