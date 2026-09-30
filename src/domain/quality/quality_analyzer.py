from src.domain.dtos.document_content_dto import DocumentContentDTO
from src.domain.dtos.laya_decision_result_dto import LayaDecisionResultDTO
from src.domain.dtos.parsed_response_dto import ParsedResponseDTO
from src.domain.dtos.quality_result_dto import QualityResultDTO
from src.domain.enums.quality_dimension import QualityDimension
from src.domain.enums.quality_level import QualityLevel
from src.domain.exceptions.quality_errors import QualityAnalysisFailed
from src.domain.ports.llm_generator_port import LlmGeneratorPort
from src.domain.quality.editorial_suitability_analyzer import EditorialSuitabilityAnalyzer
from src.domain.quality.quality_response_parser import QualityResponseParser
from src.domain.quality.quality_text_sampler import QualityTextSampler


class QualityAnalyzer:
    """Domain service that scores 4 quality dimensions from Laya and adds LLM feedback on demand."""

    def __init__(
        self,
        llm_generator: LlmGeneratorPort,
        text_sampler: QualityTextSampler,
        response_parser: QualityResponseParser,
        clarity_coherence_prompt_template: str,
        argumentation_conclusions_prompt_template: str,
        editorial_suitability_analyzer: EditorialSuitabilityAnalyzer,
    ) -> None:
        self._llm_generator = llm_generator
        self._text_sampler = text_sampler
        self._response_parser = response_parser
        self._clarity_coherence_prompt_template = clarity_coherence_prompt_template
        self._argumentation_conclusions_prompt_template = argumentation_conclusions_prompt_template
        self._editorial_suitability_analyzer = editorial_suitability_analyzer

    def analyze(
        self, document_content: DocumentContentDTO, laya_decision: LayaDecisionResultDTO
    ) -> QualityResultDTO:
        """Score quality from Laya; request LLM feedback only for dimensions below GOOD."""
        text_sample = self._text_sampler.build_sample(document_content=document_content)

        scores = {
            QualityDimension.CLARITY: laya_decision.score_clarity.expected_value,
            QualityDimension.COHERENCE: laya_decision.score_coherence.expected_value,
            QualityDimension.ARGUMENTATION: laya_decision.score_argumentation.expected_value,
            QualityDimension.CONCLUSIONS: laya_decision.score_conclusions.expected_value,
        }
        feedback = self._request_feedback_for_low_dimensions(scores=scores, text_sample=text_sample)

        overall_score = sum(scores.values()) / len(scores)
        quality_level = QualityLevel.from_score(overall_score)

        editorial_suitability = self._editorial_suitability_analyzer.analyze(
            text_sample=text_sample, laya_decision=laya_decision
        )

        return QualityResultDTO(
            overall_score=overall_score,
            quality_level=quality_level,
            dimension_scores={
                dimension.value: {"score": scores[dimension], "feedback": feedback[dimension]}
                for dimension in QualityDimension
            },
            editorial_suitability=editorial_suitability,
        )

    def _request_feedback_for_low_dimensions(
        self, scores: dict[QualityDimension, float], text_sample: str
    ) -> dict[QualityDimension, str]:
        feedback = dict.fromkeys(QualityDimension, "")
        prompt_templates_by_dimensions = (
            (
                self._clarity_coherence_prompt_template,
                (QualityDimension.CLARITY, QualityDimension.COHERENCE),
            ),
            (
                self._argumentation_conclusions_prompt_template,
                (QualityDimension.ARGUMENTATION, QualityDimension.CONCLUSIONS),
            ),
        )
        for prompt_template, dimensions in prompt_templates_by_dimensions:
            low_dimensions = tuple(
                dimension
                for dimension in dimensions
                if scores[dimension] < QualityLevel.GOOD.min_threshold
            )
            if not low_dimensions:
                continue

            prompt = self._render_prompt(template=prompt_template, text_sample=text_sample)
            parsed_response = self._response_parser.parse(
                text=self._llm_generator.generate(prompt=prompt)
            )
            self._ensure_call_produced_usable_content(
                parsed_response=parsed_response, relevant_dimensions=low_dimensions
            )
            for dimension in low_dimensions:
                feedback[dimension] = parsed_response.scores[dimension].feedback
        return feedback

    def _ensure_call_produced_usable_content(
        self,
        parsed_response: ParsedResponseDTO,
        relevant_dimensions: tuple[QualityDimension, ...],
    ) -> None:
        if not any(
            dimension in parsed_response.matched_dimensions for dimension in relevant_dimensions
        ):
            raise QualityAnalysisFailed()

    def _render_prompt(self, template: str, text_sample: str) -> str:
        return template.format(text_sample=text_sample)
