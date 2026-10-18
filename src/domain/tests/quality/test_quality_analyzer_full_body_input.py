from unittest import TestCase

from src.domain.dtos.article_body_dto import ArticleBodyDTO
from src.domain.dtos.document_content_dto import DocumentContentDTO
from src.domain.dtos.quality_level_thresholds_dto import QualityLevelThresholdsDTO
from src.domain.exceptions.quality_errors import QualityAnalysisFailed
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
        max_output_tokens=300,
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
        max_output_tokens=4096,
    )


def build_document_content(
    body: ArticleBodyDTO | None, title: str = "Header Title"
) -> DocumentContentDTO:
    return DocumentContentDTO(word_count=0, char_count=0, title=title, body=body)


class TestQualityAnalyzerFullBodyInput(TestCase):
    def setUp(self):
        self.quality_adapter = FakeLlmGeneratorAdapter([VALID_RESPONSE_ONE, VALID_RESPONSE_TWO])
        self.suitability_adapter = FakeLlmGeneratorAdapter(
            [SUITABILITY_CONTRIBUTION_RESPONSE, SUITABILITY_ALIGNMENT_RESPONSE]
        )
        self.analyzer = build_analyzer(self.quality_adapter, self.suitability_adapter)

    def test_both_quality_prompts_receive_the_whole_body_text(self):
        body = ArticleBodyDTO(
            title="Body Title",
            abstract_paragraphs=(),
            paragraphs=("First paragraph.", "Last paragraph."),
        )

        self.analyzer.analyze(build_document_content(body))

        self.assertIn(body.text_with_tables, self.quality_adapter.received_prompts[0])
        self.assertIn(body.text_with_tables, self.quality_adapter.received_prompts[1])

    def test_editorial_suitability_prompts_receive_the_whole_body_text(self):
        body = ArticleBodyDTO(
            title="Body Title",
            abstract_paragraphs=(),
            paragraphs=("First paragraph.", "Last paragraph."),
        )

        self.analyzer.analyze(build_document_content(body))

        self.assertIn(body.text_with_tables, self.suitability_adapter.received_prompts[0])
        self.assertIn(body.text_with_tables, self.suitability_adapter.received_prompts[1])

    def test_body_of_200000_characters_reaches_every_prompt_uncut(self):
        body = ArticleBodyDTO(
            title="Title",
            abstract_paragraphs=(),
            paragraphs=("x" * 99_989 + " MIDDLE", "y" * 99_989 + " ENDMARK"),
        )
        self.assertEqual(len(body.text), 200_000)

        self.analyzer.analyze(build_document_content(body))

        for prompt in [
            *self.quality_adapter.received_prompts,
            *self.suitability_adapter.received_prompts,
        ]:
            self.assertTrue(
                body.text_with_tables in prompt, "the full body must reach the prompt uncut"
            )

    def test_body_title_appears_once_and_document_title_is_not_sent(self):
        body = ArticleBodyDTO(
            title="Body Title",
            abstract_paragraphs=(),
            paragraphs=("First paragraph.",),
        )

        self.analyzer.analyze(build_document_content(body, title="Header Title"))

        for prompt in self.quality_adapter.received_prompts:
            self.assertEqual(prompt.count("Body Title"), 1)
            self.assertNotIn("Header Title", prompt)

    def test_missing_body_raises_quality_analysis_failed_without_calling_the_llm(self):
        with self.assertRaises(QualityAnalysisFailed):
            self.analyzer.analyze(build_document_content(None))

        self.assertEqual(self.quality_adapter.call_count, 0)
        self.assertEqual(self.suitability_adapter.call_count, 0)
