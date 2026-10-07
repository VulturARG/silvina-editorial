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


class CharacterizationReportInput:
    """Builds a comprehensive ReportInputDTO exercising all docx report branches."""

    @staticmethod
    def build(include_classification_reasoning: bool = True) -> ReportInputDTO:
        """Create a complete ReportInputDTO covering all export formatting features."""
        classification_reasoning = (
            "El documento sigue la estructura IMRyD y presenta metodología experimental clara."
            if include_classification_reasoning
            else ""
        )
        return ReportInputDTO(
            filename="sample_article.docx",
            document_content=DocumentContentDTO(
                word_count=2500,
                char_count=15000,
                paragraph_count=42,
                title="El Impacto de la Inteligencia Artificial en la Edición Científica",
                authors="Juan Pérez, María Gómez",
                abstract="Un resumen analítico del artículo.",
                keywords=["inteligencia artificial", "edición científica", "publicaciones"],
            ),
            classification=ClassificationResultDTO(
                article_type=ArticleType.SCIENTIFIC,
                article_size=ArticleSize.SHORT,
                confidence=0.92,
                reasoning=classification_reasoning,
                timestamp=FIXED_TIMESTAMP,
            ),
            quality=QualityResultDTO(
                overall_score=8.4,
                quality_level=QualityLevel.GOOD,
                dimension_scores={
                    "claridad": {
                        "score": 8.5,
                        "feedback": "Texto claro y bien estructurado en sus secciones principales.",
                        "feedback_blocks": [
                            {
                                "kind": "title",
                                "level": 0,
                                "marker": "",
                                "text": "Fortalezas del manuscrito",
                            },
                            {
                                "kind": "item",
                                "level": 0,
                                "marker": "•",
                                "text": "Primer aspecto positivo con **negrita** y *cursiva* destacada.",
                            },
                            {
                                "kind": "item",
                                "level": 1,
                                "marker": "•",
                                "text": "Segundo aspecto positivo detallado en subnivel uno.",
                            },
                            {
                                "kind": "item",
                                "level": 2,
                                "marker": "1.",
                                "text": "Tercer aspecto con marcador numerado en subnivel dos.",
                            },
                            {
                                "kind": "plain",
                                "level": 0,
                                "marker": "",
                                "text": "Observación complementaria en formato de texto plano con **énfasis**.",
                            },
                        ],
                    },
                    "coherencia": {
                        "score": 8.0,
                        "feedback": "Argumentos consistentes y lógica expositiva **sólida** a lo largo del manuscrito.",
                    },
                },
                timestamp=FIXED_TIMESTAMP,
                editorial_suitability=EditorialSuitabilityDTO(
                    contribution_verdict="Aporte relevante",
                    contribution_phrase="Presenta un marco de análisis original",
                    contribution_observation="La contribución al campo disciplinar es clara y sustentada.",
                    alignment_verdict="Alineado",
                    alignment_lines="Línea 1: Innovación Editorial, Línea 2: Tecnologías Lingüísticas",
                    alignment_justification="El contenido coincide plenamente con las líneas temáticas prioritarias.",
                ),
            ),
            grammar=GrammarCheckResultDTO(
                score=7.5,
                feedback="Redacción aceptable con observaciones puntuales.",
                errors=[
                    GrammarErrorDTO(
                        number=1,
                        message="Posible error de concordancia en el sintagma nominal.",
                        context="los datos recopilados durante el estudio fue analizados exhaustivamente",
                        offset=52,
                        length=13,
                        replacements=["fueron", "habían sido"],
                    ),
                    GrammarErrorDTO(
                        number=2,
                        message="Puntuación inadecuada al cierre de oración.",
                        context="el resultado final se presenta a continuación,",
                        offset=180,
                        length=1,
                        replacements=[],
                    ),
                ],
            ),
            structure=StructureValidationResultDTO(
                is_valid=False,
                missing_sections=["conclusiones", "referencias"],
                section_details={
                    "introduccion": {"present": True},
                    "metodologia": {"present": True},
                    "conclusiones": {"present": False},
                },
                timestamp=FIXED_TIMESTAMP,
            ),
            citations=CitationAnalysisResultDTO(
                total_citations=10,
                total_references=8,
                matched_count=7,
                unmatched_count=3,
                citations_by_type={"parenthetical": 6, "narrative": 4},
                unmatched_citations=["(Smith, 2020)", "(Lopez, 2019)", "(Diaz, 2021)"],
                timestamp=FIXED_TIMESTAMP,
            ),
            apa_validation=ApaValidationResultDTO(
                is_valid=False,
                violation_count=2,
                violations=[
                    ApaViolationDTO(
                        citation_text="(Smith, 2020)",
                        error_type=ApaErrorType.COMMA_ERROR,
                        location=145,
                        explanation="Falta punto y coma antes del año en formato específico.",
                        correction="(Smith; 2020)",
                        paragraph_preview="...según datos de Smith (2020)...",
                    ),
                    ApaViolationDTO(
                        citation_text="(Lopez y Diaz, 2019)",
                        error_type=ApaErrorType.ET_AL_FORMAT_ERROR,
                        location=310,
                        explanation="Formato de múltiples autores incorrecto para más de dos autores en texto.",
                        correction="",
                        paragraph_preview="...como demostraron (Lopez y Diaz, 2019)...",
                    ),
                ],
            ),
            recommendations=[
                RecommendationDTO(
                    priority=RecommendationPriority.HIGH,
                    message="Incorporar la sección obligatoria de conclusiones.",
                ),
                RecommendationDTO(
                    priority=RecommendationPriority.MEDIUM,
                    message="Corregir las citas en texto observadas según normativa APA 7.",
                ),
                RecommendationDTO(
                    priority=RecommendationPriority.LOW,
                    message="Ajustar la concordancia gramatical y conectores redundantes señalados.",
                ),
            ],
            verdict=PublicationVerdictDTO(
                verdict=PublicationVerdict.WARNING,
                message="⚠️ REQUIERE REVISIÓN antes de publicación.",
            ),
            eumic_violations=[
                EumicViolationDTO(
                    category="estructura",
                    message="Falta sección obligatoria de conclusiones.",
                    severity=SeverityLevel.WARNING,
                    details="La estructura debe contener la sección conclusiones según directrices editoriales.",
                ),
            ],
        )
