from src.domain.classification.article_classification_response_parser import (
    ArticleClassificationResponseParser,
)
from src.domain.classification.research_intent_detector_port import (
    ResearchIntentDetectorPort,
)
from src.domain.ports.llm_generator_port import LlmGeneratorPort


class OllamaResearchIntentAdapter(ResearchIntentDetectorPort):
    """Detects research intent signals using an LLM generator backend."""

    def __init__(
        self,
        llm_generator: LlmGeneratorPort,
        response_parser: ArticleClassificationResponseParser,
        signal_prompt_template: str,
        temperature: float = 0.1,
        num_predict: int = 150,
    ) -> None:
        self._llm_generator = llm_generator
        self._response_parser = response_parser
        self._signal_prompt_template = signal_prompt_template
        self._temperature = temperature
        self._num_predict = num_predict

    def detect(self, text_sample: str, title: str | None) -> tuple[bool, bool, bool]:
        """Detect research intent signals using an LLM generator and prompt template."""
        prompt = self._signal_prompt_template.format(title=title, text_sample=text_sample)
        response_text = self._llm_generator.generate(
            prompt=prompt,
            options={"temperature": self._temperature, "num_predict": self._num_predict},
        )
        return self._response_parser.parse(response_text=response_text)
