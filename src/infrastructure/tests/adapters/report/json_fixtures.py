from datetime import datetime

from src.domain.dtos.apa_validation_result_dto import ApaValidationResultDTO
from src.domain.dtos.apa_violation_dto import ApaViolationDTO
from src.domain.dtos.citation_analysis_result_dto import CitationAnalysisResultDTO
from src.domain.dtos.classification_result_dto import ClassificationResultDTO
from src.domain.dtos.document_content_dto import DocumentContentDTO
from src.domain.dtos.editorial_suitability_dto import EditorialSuitabilityDTO
from src.domain.dtos.eumic_violation_dto import EumicViolationDTO
from src.domain.dtos.grammar_check_result_dto import GrammarCheckResultDTO
from src.domain.dtos.grammar_error_dto import GrammarErrorDTO
from src.domain.dtos.publication_verdict_dto import PublicationVerdictDTO
from src.domain.dtos.quality_result_dto import QualityResultDTO
from src.domain.dtos.recommendation_dto import RecommendationDTO
from src.domain.dtos.report_input_dto import ReportInputDTO
from src.domain.dtos.structure_validation_result_dto import StructureValidationResultDTO
from src.domain.enums.apa_error_type import ApaErrorType
from src.domain.enums.article_size import ArticleSize
from src.domain.enums.article_type import ArticleType
from src.domain.enums.publication_verdict import PublicationVerdict
from src.domain.enums.quality_level import QualityLevel
from src.domain.enums.recommendation_priority import RecommendationPriority
from src.domain.enums.severity_level import SeverityLevel

FIXED_TIMESTAMP = datetime(2024, 1, 15, 10, 30, 0)


class JsonReportFixtures:
    """Builds real (non-mock) ReportInputDTO trees for JSON adapter tests."""

    @staticmethod
    def make_real_report_input_dto(**overrides) -> ReportInputDTO:
        """Build a real ReportInputDTO with fixed, non-random nested DTO values."""
        defaults = {
            "filename": "sample_article.docx",
            "document_content": DocumentContentDTO(
                word_count=2500,
                char_count=15000,
                paragraph_count=42,
                title="El Impacto de la Inteligencia Artificial",
                authors="Juan Perez, Maria Gomez",
                abstract="Un resumen del articulo.",
                keywords=["inteligencia artificial", "editorial"],
            ),
            "classification": ClassificationResultDTO(
                article_type=ArticleType.SCIENTIFIC,
                article_size=ArticleSize.SHORT,
                confidence=0.92,
                reasoning="El documento sigue la estructura IMRyD.",
                timestamp=FIXED_TIMESTAMP,
            ),
            "quality": QualityResultDTO(
                overall_score=8.4,
                quality_level=QualityLevel.GOOD,
                dimension_scores={
                    "claridad": {"score": 8.0, "feedback": "Texto claro y bien estructurado."},
                    "coherencia": {"score": 8.8, "feedback": "Argumentos consistentes."},
                },
                timestamp=FIXED_TIMESTAMP,
                editorial_suitability=EditorialSuitabilityDTO(
                    contribution_verdict="Aporte relevante",
                    contribution_phrase="Presenta un enfoque novedoso",
                    contribution_observation="La contribucion es clara.",
                    alignment_verdict="Alineado",
                    alignment_lines="Linea 1, Linea 2",
                    alignment_justification="Coincide con las lineas editoriales.",
                ),
            ),
            "grammar": GrammarCheckResultDTO(
                score=9.0,
                feedback="Muy buena redaccion.",
                errors=[
                    GrammarErrorDTO(
                        number=1,
                        message="Posible error de concordancia.",
                        context="los datos fue analizados",
                        offset=120,
                        length=13,
                        replacements=["fueron"],
                    )
                ],
            ),
            "structure": StructureValidationResultDTO(
                is_valid=False,
                missing_sections=["conclusiones"],
                section_details={"introduccion": {"present": True}},
                timestamp=FIXED_TIMESTAMP,
            ),
            "citations": CitationAnalysisResultDTO(
                total_citations=10,
                total_references=8,
                matched_count=7,
                unmatched_count=3,
                citations_by_type={"parenthetical": 6, "narrative": 4},
                unmatched_citations=["(Smith, 2020)", "(Lopez, 2019)", "(Diaz, 2021)"],
                timestamp=FIXED_TIMESTAMP,
            ),
            "apa_validation": ApaValidationResultDTO(
                is_valid=False,
                violation_count=2,
                violations=[
                    ApaViolationDTO(
                        citation_text="(Smith, 2020)",
                        error_type=ApaErrorType.COMMA_ERROR,
                        location=145,
                        explanation="Falta punto y coma antes del anio.",
                        correction="(Smith; 2020)",
                        paragraph_preview="...segun Smith (2020)...",
                    ),
                    ApaViolationDTO(
                        citation_text="(Lopez y Diaz, 2019)",
                        error_type=ApaErrorType.ET_AL_FORMAT_ERROR,
                        location=310,
                        explanation="Formato de multiples autores incorrecto.",
                        correction="(Lopez & Diaz, 2019)",
                    ),
                ],
            ),
            "recommendations": [
                RecommendationDTO(
                    priority=RecommendationPriority.HIGH, message="Agregar conclusiones."
                ),
                RecommendationDTO(
                    priority=RecommendationPriority.MEDIUM, message="Revisar citas APA."
                ),
                RecommendationDTO(
                    priority=RecommendationPriority.LOW, message="Ajustar estilo de redaccion."
                ),
            ],
            "verdict": PublicationVerdictDTO(
                verdict=PublicationVerdict.WARNING,
                message="Requiere revision antes de publicacion.",
            ),
            "eumic_violations": [
                EumicViolationDTO(
                    category="estructura",
                    message="Falta seccion de conclusiones.",
                    severity=SeverityLevel.WARNING,
                    details="La seccion de conclusiones es obligatoria.",
                )
            ],
        }
        defaults.update(overrides)
        return ReportInputDTO(**defaults)
