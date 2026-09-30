from src.domain.dtos.editorial_suitability_dto import EditorialSuitabilityDTO
from src.domain.dtos.laya_decision_result_dto import LayaDecisionResultDTO
from src.domain.enums.editorial_alignment_verdict import EditorialAlignmentVerdict
from src.domain.enums.laya_editorial_verdict import LayaEditorialVerdict
from src.domain.enums.laya_research_line_answer import LayaResearchLineAnswer
from src.domain.ports.llm_generator_port import LlmGeneratorPort
from src.domain.quality.editorial_suitability_parser import EditorialSuitabilityParser

_DEFAULT_GENERATION_OPTIONS = {"temperature": 0.1, "num_predict": 300}


class EditorialSuitabilityAnalyzer:
    """Stateless domain service coordinating contribution and alignment evaluations."""

    def __init__(
        self,
        llm_generator: LlmGeneratorPort,
        parser: EditorialSuitabilityParser,
        contribution_prompt_template: str,
        alignment_prompt_template: str,
        research_lines: str,
        generation_options: dict | None = None,
    ) -> None:
        self._llm_generator = llm_generator
        self._parser = parser
        self._contribution_prompt_template = contribution_prompt_template
        self._alignment_prompt_template = alignment_prompt_template
        self._research_lines = research_lines
        self._generation_options = (
            generation_options if generation_options is not None else _DEFAULT_GENERATION_OPTIONS
        )

    def analyze(
        self, text_sample: str, laya_decision: LayaDecisionResultDTO
    ) -> EditorialSuitabilityDTO:
        """Evaluate contribution and alignment suitability using Laya and on-demand LLM narrative."""
        contribution_verdict, contribution_phrase, contribution_observation = (
            self._evaluate_contribution(
                text_sample=text_sample,
                editorial_verdict=laya_decision.editorial_verdict.answer,
            )
        )
        alignment_verdict, alignment_lines, alignment_justification = self._evaluate_alignment(
            text_sample=text_sample,
            research_line=laya_decision.research_line.answer,
        )
        return EditorialSuitabilityDTO(
            contribution_verdict=contribution_verdict,
            contribution_phrase=contribution_phrase,
            contribution_observation=contribution_observation,
            alignment_verdict=alignment_verdict,
            alignment_lines=alignment_lines,
            alignment_justification=alignment_justification,
        )

    def _evaluate_contribution(
        self, text_sample: str, editorial_verdict: str
    ) -> tuple[str, str, str]:
        """Evaluate contribution verdict, phrase, and observation."""
        if editorial_verdict == LayaEditorialVerdict.SUSTAINED.value:
            phrase = ""
        else:
            phrase = self._request_contribution_phrase(text_sample=text_sample)
        observation = self._parser.build_contribution_observation(
            verdict=editorial_verdict, phrase=phrase
        )
        return editorial_verdict, phrase, observation

    def _request_contribution_phrase(self, text_sample: str) -> str:
        """Request and parse a contribution phrase from the language model."""
        contribution_prompt = self._contribution_prompt_template.format(text_sample=text_sample)
        contribution_response = self._llm_generator.generate(
            prompt=contribution_prompt, options=self._generation_options
        )
        _, phrase, _ = self._parser.parse_contribution(contribution_response)
        return phrase

    def _evaluate_alignment(self, text_sample: str, research_line: str) -> tuple[str, str, str]:
        """Evaluate alignment verdict, line title, and justification."""
        if research_line != LayaResearchLineAnswer.NONE.value:
            alignment_lines = self._parser.resolve_research_line_title(
                research_lines=self._research_lines, line_id=research_line
            )
            return EditorialAlignmentVerdict.ALIGNED.value, alignment_lines, ""
        return self._request_alignment_narrative(text_sample=text_sample)

    def _request_alignment_narrative(self, text_sample: str) -> tuple[str, str, str]:
        """Request and parse alignment narrative from the language model."""
        alignment_prompt = self._alignment_prompt_template.format(
            text_sample=text_sample, research_lines=self._research_lines
        )
        alignment_response = self._llm_generator.generate(
            prompt=alignment_prompt, options=self._generation_options
        )
        _, alignment_lines, alignment_justification = self._parser.parse_alignment(
            alignment_response
        )
        return (
            EditorialAlignmentVerdict.NOT_ALIGNED.value,
            alignment_lines,
            alignment_justification,
        )
