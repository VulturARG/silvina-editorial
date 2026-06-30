from dataclasses import dataclass

from src.domain.dtos.apa_validation_result_dto import ApaValidationResultDTO
from src.domain.dtos.base_dto import BaseDTO
from src.domain.dtos.citation_analysis_result_dto import CitationAnalysisResultDTO
from src.domain.dtos.classification_result_dto import ClassificationResultDTO
from src.domain.dtos.document_content_dto import DocumentContentDTO
from src.domain.dtos.grammar_check_result_dto import GrammarCheckResultDTO
from src.domain.dtos.quality_result_dto import QualityResultDTO
from src.domain.dtos.structure_validation_result_dto import StructureValidationResultDTO

_PUBLISH_THRESHOLD = 7.0


@dataclass(frozen=True)
class ReportInputDTO(BaseDTO):
    """Aggregates all analysis results required to generate an export report."""

    filename: str
    document_content: DocumentContentDTO
    classification: ClassificationResultDTO
    quality: QualityResultDTO
    grammar: GrammarCheckResultDTO
    structure: StructureValidationResultDTO
    citations: CitationAnalysisResultDTO
    apa_validation: ApaValidationResultDTO
    recommendations: list  # TODO Slice 13: replace with list[RecommendationDTO]

    @property
    def is_publishable(self) -> bool:
        return (
            self.quality.overall_score >= _PUBLISH_THRESHOLD
            and self.grammar.score >= _PUBLISH_THRESHOLD
            and self.structure.is_valid
            and len(self.apa_validation.violations) == 0
            and self.citations.total_citations > 0
        )

    @property
    def publishability_reason(self) -> str:
        if self.citations.total_citations == 0:
            return "No se detectaron citas APA en el texto. Verifique el formato de citación según normas APA 7."
        apa_count = len(self.apa_validation.violations)
        quality_score = self.quality.overall_score
        grammar_score = self.grammar.score
        if self.is_publishable:
            return "El documento cumple con todos los estándares de calidad, estructura y formato APA 7 requeridos por las normas EUMIC."
        if (
            apa_count > 0
            or grammar_score < _PUBLISH_THRESHOLD
            or quality_score < _PUBLISH_THRESHOLD
        ):
            return f"El documento requiere revisión. Calidad: {quality_score:.1f}/10, Gramática: {grammar_score:.1f}/10, Errores APA: {apa_count}."
        if not self.structure.is_valid:
            return "Estructura incompleta según normas EUMIC. Complete las secciones faltantes."
        return "El documento requiere mejoras antes de la publicación."
