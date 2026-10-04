from src.domain.dtos.editorial_suitability_dto import EditorialSuitabilityDTO
from src.domain.ports.llm_generator_port import LlmGeneratorPort
from src.domain.quality.editorial_suitability_parser import EditorialSuitabilityParser


class EditorialSuitabilityAnalyzer:
    """Stateless domain service coordinating contribution and alignment LLM evaluations."""

    def __init__(
        self,
        llm_generator: LlmGeneratorPort,
        parser: EditorialSuitabilityParser,
        contribution_prompt_template: str,
        alignment_prompt_template: str,
        research_lines: str,
        temperature: float,
        num_predict: int,
    ) -> None:
        self._llm_generator = llm_generator
        self._parser = parser
        self._contribution_prompt_template = contribution_prompt_template
        self._alignment_prompt_template = alignment_prompt_template
        self._research_lines = research_lines
        self._temperature = temperature
        self._num_predict = num_predict

    def analyze(self, text_sample: str) -> EditorialSuitabilityDTO:
        """Evaluate contribution and alignment suitability for the given text sample."""
        contribution_prompt = self._contribution_prompt_template.format(text_sample=text_sample)
        contribution_response = self._llm_generator.generate(
            prompt=contribution_prompt, options=self._generation_options()
        )
        contribution_verdict, contribution_phrase, contribution_observation = (
            self._parser.parse_contribution(contribution_response)
        )

        alignment_prompt = self._alignment_prompt_template.format(
            text_sample=text_sample, research_lines=self._research_lines
        )
        alignment_response = self._llm_generator.generate(
            prompt=alignment_prompt, options=self._generation_options()
        )
        alignment_verdict, alignment_lines, alignment_justification = self._parser.parse_alignment(
            alignment_response
        )

        return EditorialSuitabilityDTO(
            contribution_verdict=contribution_verdict,
            contribution_phrase=contribution_phrase,
            contribution_observation=contribution_observation,
            alignment_verdict=alignment_verdict,
            alignment_lines=alignment_lines,
            alignment_justification=alignment_justification,
        )

    def _generation_options(self) -> dict:
        return {"temperature": self._temperature, "num_predict": self._num_predict}
