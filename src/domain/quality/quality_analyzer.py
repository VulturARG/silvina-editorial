from src.domain.dtos.document_content_dto import DocumentContentDTO
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
    """Domain service that orchestrates LLM-backed quality scoring across 4 dimensions."""

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

    def analyze(self, document_content: DocumentContentDTO) -> QualityResultDTO:
        """Score document quality across Claridad, Coherencia, Argumentación and Conclusiones."""
        text_sample = self._text_sampler.build_sample(document_content=document_content)

        clarity_coherence_prompt = self._render_prompt(
            template=self._clarity_coherence_prompt_template, text_sample=text_sample
        )
        argumentation_conclusions_prompt = self._render_prompt(
            template=self._argumentation_conclusions_prompt_template, text_sample=text_sample
        )

        clarity_coherence_response = self._llm_generator.generate(prompt=clarity_coherence_prompt)
        argumentation_conclusions_response = self._llm_generator.generate(
            prompt=argumentation_conclusions_prompt
        )

        clarity_coherence_parsed = self._response_parser.parse(text=clarity_coherence_response)
        self._ensure_call_produced_usable_content(
            parsed_response=clarity_coherence_parsed,
            relevant_dimensions=(QualityDimension.CLARITY, QualityDimension.COHERENCE),
        )

        argumentation_conclusions_parsed = self._response_parser.parse(
            text=argumentation_conclusions_response
        )
        self._ensure_call_produced_usable_content(
            parsed_response=argumentation_conclusions_parsed,
            relevant_dimensions=(QualityDimension.ARGUMENTATION, QualityDimension.CONCLUSIONS),
        )

        dimension_scores = {
            QualityDimension.CLARITY: clarity_coherence_parsed.scores[QualityDimension.CLARITY],
            QualityDimension.COHERENCE: clarity_coherence_parsed.scores[QualityDimension.COHERENCE],
            QualityDimension.ARGUMENTATION: argumentation_conclusions_parsed.scores[
                QualityDimension.ARGUMENTATION
            ],
            QualityDimension.CONCLUSIONS: argumentation_conclusions_parsed.scores[
                QualityDimension.CONCLUSIONS
            ],
        }

        overall_score = sum(d.score for d in dimension_scores.values()) / len(dimension_scores)
        quality_level = QualityLevel.from_score(overall_score)

        editorial_suitability = self._editorial_suitability_analyzer.analyze(
            text_sample=text_sample
        )

        return QualityResultDTO(
            overall_score=overall_score,
            quality_level=quality_level,
            dimension_scores={
                dimension.value: {
                    "score": value.score,
                    "feedback": value.feedback,
                    "feedback_blocks": [
                        {
                            "kind": block.kind.value,
                            "text": block.text,
                            "level": block.level,
                            "marker": block.marker,
                        }
                        for block in value.feedback_blocks
                    ],
                }
                for dimension, value in dimension_scores.items()
            },
            editorial_suitability=editorial_suitability,
        )

    def _ensure_call_produced_usable_content(
        self,
        parsed_response: ParsedResponseDTO,
        relevant_dimensions: tuple[QualityDimension, QualityDimension],
    ) -> None:
        if not any(
            dimension in parsed_response.matched_dimensions for dimension in relevant_dimensions
        ):
            raise QualityAnalysisFailed()

    def _render_prompt(self, template: str, text_sample: str) -> str:
        return template.format(text_sample=text_sample)
