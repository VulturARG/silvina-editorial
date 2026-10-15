from unittest import TestCase

from src.domain.dtos.article_body_dto import ArticleBodyDTO
from src.domain.dtos.document_content_dto import DocumentContentDTO
from src.domain.dtos.quality_level_thresholds_dto import QualityLevelThresholdsDTO
from src.domain.enums.quality_level import QualityLevel
from src.domain.quality.editorial_suitability_analyzer import EditorialSuitabilityAnalyzer
from src.domain.quality.quality_analyzer import QualityAnalyzer
from src.domain.tests.quality.editorial_suitability_parser_builder_for_test import (
    EditorialSuitabilityParserBuilderForTest,
)
from src.domain.tests.quality.fake_llm_generator_adapter import FakeLlmGeneratorAdapter
from src.domain.tests.quality.quality_response_parser_builder_for_test import (
    QualityResponseParserBuilderForTest,
)

CLARITY_COHERENCE_PROMPT_TEMPLATE = "Evalua claridad y coherencia.\nTEXTO:\n{text_sample}"
ARGUMENTATION_CONCLUSIONS_PROMPT_TEMPLATE = (
    "Evalua argumentacion y conclusiones.\nTEXTO:\n{text_sample}"
)
SUITABILITY_CONTRIBUTION_PROMPT_TEMPLATE = "Evalua contribucion.\n{text_sample}"
SUITABILITY_ALIGNMENT_PROMPT_TEMPLATE = "Evalua alineacion.\n{research_lines}\n{text_sample}"
SUITABILITY_RESEARCH_LINES = "1. Linea de prueba uno\n2. Linea de prueba dos"

SUITABILITY_CONTRIBUTION_RESPONSE = (
    "VEREDICTO: SUSTENTADA\n"
    "CONTRIBUCION: Propone un marco de analisis original.\n"
    "OBSERVACION: sera ignorada.\n"
)
SUITABILITY_ALIGNMENT_RESPONSE = (
    "VEREDICTO: ALINEADO\n"
    "LINEAS: Linea 1 y 2.\n"
    "JUSTIFICACION: Se relaciona con las lineas mencionadas.\n"
)

CLARITY_COHERENCE_RESPONSE = """**1. Claridad del argumento** [Puntuación: 8/10]
El argumento central es claro y facil de seguir en todo el texto.

**2. Coherencia** [Puntuación: 7/10]
Las ideas se conectan logicamente entre las distintas secciones del texto.
"""

ARGUMENTATION_CONCLUSIONS_RESPONSE = """**1. Argumentación** [Puntuación: 8/10]
Los argumentos presentados son solidos y estan bien fundamentados.

**2. Conclusiones** [Puntuación: 7/10]
Las conclusiones se desprenden claramente del contenido desarrollado.
"""


def build_analyzer(quality_level_thresholds: QualityLevelThresholdsDTO) -> QualityAnalyzer:
    suitability_adapter = FakeLlmGeneratorAdapter(
        [SUITABILITY_CONTRIBUTION_RESPONSE, SUITABILITY_ALIGNMENT_RESPONSE]
    )
    editorial_suitability_analyzer = EditorialSuitabilityAnalyzer(
        llm_generator=suitability_adapter,
        parser=EditorialSuitabilityParserBuilderForTest().build(),
        contribution_prompt_template=SUITABILITY_CONTRIBUTION_PROMPT_TEMPLATE,
        alignment_prompt_template=SUITABILITY_ALIGNMENT_PROMPT_TEMPLATE,
        research_lines=SUITABILITY_RESEARCH_LINES,
        temperature=0.1,
        num_predict=300,
    )
    return QualityAnalyzer(
        llm_generator=FakeLlmGeneratorAdapter(
            [CLARITY_COHERENCE_RESPONSE, ARGUMENTATION_CONCLUSIONS_RESPONSE]
        ),
        response_parser=QualityResponseParserBuilderForTest().build(),
        clarity_coherence_prompt_template=CLARITY_COHERENCE_PROMPT_TEMPLATE,
        argumentation_conclusions_prompt_template=ARGUMENTATION_CONCLUSIONS_PROMPT_TEMPLATE,
        editorial_suitability_analyzer=editorial_suitability_analyzer,
        quality_level_thresholds=quality_level_thresholds,
    )


def build_document_content() -> DocumentContentDTO:
    body = ArticleBodyDTO(
        title="Title", abstract_paragraphs=(), paragraphs=("Parrafo uno.", "Parrafo dos.")
    )
    return DocumentContentDTO(word_count=4, char_count=24, title="Title", body=body)


def classify_overall_score(quality_level_thresholds: QualityLevelThresholdsDTO) -> QualityLevel:
    analyzer = build_analyzer(quality_level_thresholds)
    return analyzer.analyze(build_document_content()).quality_level


class TestQualityAnalyzerQualityLevelThresholds(TestCase):
    def test_overall_score_of_seven_point_five_is_excellent_under_lenient_thresholds(self):
        lenient_thresholds = QualityLevelThresholdsDTO(
            excellent_threshold=7.0,
            good_threshold=6.0,
            acceptable_threshold=4.0,
            needs_improvement_threshold=2.0,
        )

        self.assertEqual(classify_overall_score(lenient_thresholds), QualityLevel.EXCELLENT)

    def test_overall_score_of_seven_point_five_is_acceptable_under_strict_thresholds(self):
        strict_thresholds = QualityLevelThresholdsDTO(
            excellent_threshold=9.0,
            good_threshold=8.0,
            acceptable_threshold=6.0,
            needs_improvement_threshold=4.0,
        )

        self.assertEqual(classify_overall_score(strict_thresholds), QualityLevel.ACCEPTABLE)
