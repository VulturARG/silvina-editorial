from unittest import TestCase

from src.domain.dtos.article_body_dto import ArticleBodyDTO
from src.domain.dtos.body_table_dto import BodyTableDTO
from src.domain.dtos.document_content_dto import DocumentContentDTO
from src.domain.dtos.quality_level_thresholds_dto import QualityLevelThresholdsDTO
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

TABLE_MARKDOWN = "| Name | Score |\n| --- | --- |\n| Ana | 9 |"

VALID_RESPONSE_ONE = """**1. Claridad del argumento** [Puntuación: 8/10]
El argumento central es claro y facil de seguir en todo el texto.

**2. Coherencia** [Puntuación: 8/10]
Las ideas se conectan logicamente entre las distintas secciones del texto.
"""

VALID_RESPONSE_TWO = """**1. Argumentación** [Puntuación: 8/10]
Los argumentos presentados son solidos y estan bien fundamentados.

**2. Conclusiones** [Puntuación: 8/10]
Las conclusiones se desprenden claramente del contenido desarrollado.
"""

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


def build_analyzer(
    quality_adapter: FakeLlmGeneratorAdapter, suitability_adapter: FakeLlmGeneratorAdapter
) -> QualityAnalyzer:
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
        llm_generator=quality_adapter,
        response_parser=QualityResponseParserBuilderForTest().build(),
        clarity_coherence_prompt_template=CLARITY_COHERENCE_PROMPT_TEMPLATE,
        argumentation_conclusions_prompt_template=ARGUMENTATION_CONCLUSIONS_PROMPT_TEMPLATE,
        editorial_suitability_analyzer=editorial_suitability_analyzer,
        quality_level_thresholds=QualityLevelThresholdsDTO(
            excellent_threshold=9.0,
            good_threshold=7.0,
            acceptable_threshold=5.0,
            needs_improvement_threshold=3.0,
        ),
    )


def build_document_content(body: ArticleBodyDTO) -> DocumentContentDTO:
    return DocumentContentDTO(word_count=0, char_count=0, title=body.title, body=body)


class TestQualityAnalyzerTables(TestCase):
    def setUp(self):
        self.quality_adapter = FakeLlmGeneratorAdapter([VALID_RESPONSE_ONE, VALID_RESPONSE_TWO])
        self.suitability_adapter = FakeLlmGeneratorAdapter(
            [SUITABILITY_CONTRIBUTION_RESPONSE, SUITABILITY_ALIGNMENT_RESPONSE]
        )
        self.analyzer = build_analyzer(self.quality_adapter, self.suitability_adapter)

    def test_both_quality_prompts_contain_table_markdown_between_its_paragraphs(self):
        body = ArticleBodyDTO(
            title="Body Title",
            abstract_paragraphs=(),
            paragraphs=("Before.", "After."),
            tables=(BodyTableDTO(markdown=TABLE_MARKDOWN, position=1),),
        )
        expected_text_sample = f"Body Title\n\nBefore.\n\n{TABLE_MARKDOWN}\n\nAfter."

        self.analyzer.analyze(build_document_content(body))

        self.assertIn(expected_text_sample, self.quality_adapter.received_prompts[0])
        self.assertIn(expected_text_sample, self.quality_adapter.received_prompts[1])

    def test_both_editorial_suitability_prompts_contain_table_markdown_between_its_paragraphs(
        self,
    ):
        body = ArticleBodyDTO(
            title="Body Title",
            abstract_paragraphs=(),
            paragraphs=("Before.", "After."),
            tables=(BodyTableDTO(markdown=TABLE_MARKDOWN, position=1),),
        )
        expected_text_sample = f"Body Title\n\nBefore.\n\n{TABLE_MARKDOWN}\n\nAfter."

        self.analyzer.analyze(build_document_content(body))

        self.assertIn(expected_text_sample, self.suitability_adapter.received_prompts[0])
        self.assertIn(expected_text_sample, self.suitability_adapter.received_prompts[1])

    def test_table_at_the_end_of_the_body_is_placed_after_the_last_paragraph(self):
        body = ArticleBodyDTO(
            title="Body Title",
            abstract_paragraphs=(),
            paragraphs=("Only paragraph.",),
            tables=(BodyTableDTO(markdown=TABLE_MARKDOWN, position=1),),
        )
        expected_text_sample = f"Body Title\n\nOnly paragraph.\n\n{TABLE_MARKDOWN}"

        self.analyzer.analyze(build_document_content(body))

        self.assertIn(expected_text_sample, self.quality_adapter.received_prompts[0])
        self.assertIn(expected_text_sample, self.suitability_adapter.received_prompts[0])

    def test_body_without_tables_produces_the_same_prompts_as_its_text_with_tables(self):
        body = ArticleBodyDTO(
            title="Body Title",
            abstract_paragraphs=(),
            paragraphs=("First paragraph.", "Last paragraph."),
        )

        self.analyzer.analyze(build_document_content(body))

        self.assertEqual(
            self.quality_adapter.received_prompts,
            [
                CLARITY_COHERENCE_PROMPT_TEMPLATE.format(text_sample=body.text_with_tables),
                ARGUMENTATION_CONCLUSIONS_PROMPT_TEMPLATE.format(text_sample=body.text_with_tables),
            ],
        )
        self.assertEqual(
            self.suitability_adapter.received_prompts,
            [
                SUITABILITY_CONTRIBUTION_PROMPT_TEMPLATE.format(text_sample=body.text_with_tables),
                SUITABILITY_ALIGNMENT_PROMPT_TEMPLATE.format(
                    research_lines=SUITABILITY_RESEARCH_LINES,
                    text_sample=body.text_with_tables,
                ),
            ],
        )
