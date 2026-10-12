from dataclasses import dataclass

from src.domain.dtos.apa_validation_result_dto import ApaValidationResultDTO
from src.domain.dtos.base_dto import BaseDTO
from src.domain.dtos.citation_analysis_result_dto import CitationAnalysisResultDTO
from src.domain.dtos.classification_result_dto import ClassificationResultDTO
from src.domain.dtos.document_content_dto import DocumentContentDTO
from src.domain.dtos.eumic_violation_dto import EumicViolationDTO
from src.domain.dtos.grammar_check_result_dto import GrammarCheckResultDTO
from src.domain.dtos.publication_verdict_dto import PublicationVerdictDTO
from src.domain.dtos.quality_result_dto import QualityResultDTO
from src.domain.dtos.recommendation_dto import RecommendationDTO
from src.domain.dtos.structure_validation_result_dto import StructureValidationResultDTO


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
    recommendations: list[RecommendationDTO]
    verdict: PublicationVerdictDTO
    eumic_violations: list[EumicViolationDTO]

    def is_publishable(self, publish_threshold: float) -> bool:
        """Return True when every publication rule holds for the given threshold."""
        return (
            self.quality.overall_score >= publish_threshold
            and self.grammar.score >= publish_threshold
            and self.structure.is_valid
            and len(self.apa_validation.violations) == 0
            and self.citations.total_citations > 0
        )

    def publishability_reason(self, publish_threshold: float) -> str:
        """Return the message that explains the publication decision for the given threshold."""
        if self.citations.total_citations == 0:
            return "No se detectaron citas APA en el texto. Verifique el formato de citación según normas APA 7."
        apa_count = len(self.apa_validation.violations)
        quality_score = self.quality.overall_score
        grammar_score = self.grammar.score
        if self.is_publishable(publish_threshold):
            return "El documento cumple con todos los estándares de calidad, estructura y formato APA 7 requeridos por las normas EUMIC."
        if apa_count > 0 or grammar_score < publish_threshold or quality_score < publish_threshold:
            return f"El documento requiere revisión. Calidad: {quality_score:.1f}/10, Gramática: {grammar_score:.1f}/10, Errores APA: {apa_count}."
        if not self.structure.is_valid:
            return "Estructura incompleta según normas EUMIC. Complete las secciones faltantes."
        return "El documento requiere mejoras antes de la publicación."
