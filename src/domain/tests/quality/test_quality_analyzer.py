import ast
from dataclasses import replace
from pathlib import Path
from unittest import TestCase

from src.domain.dtos.document_content_dto import DocumentContentDTO
from src.domain.dtos.editorial_suitability_dto import EditorialSuitabilityDTO
from src.domain.dtos.laya_choice_decision_dto import LayaChoiceDecisionDTO
from src.domain.dtos.laya_decision_result_dto import LayaDecisionResultDTO
from src.domain.dtos.laya_score_decision_dto import LayaScoreDecisionDTO
from src.domain.enums.laya_editorial_verdict import LayaEditorialVerdict
from src.domain.enums.quality_level import QualityLevel
from src.domain.exceptions.quality_errors import QualityAnalysisFailed
from src.domain.quality.editorial_suitability_analyzer import EditorialSuitabilityAnalyzer
from src.domain.quality.editorial_suitability_parser import EditorialSuitabilityParser
from src.domain.quality.quality_analyzer import QualityAnalyzer
from src.domain.quality.quality_response_parser import QualityResponseParser
from src.domain.quality.quality_text_sampler import QualityTextSampler
from src.domain.tests.laya.fake_laya_decision_port import DEFAULT_DECISION_RESULT
from src.domain.tests.quality.fake_llm_generator_adapter import FakeLlmGeneratorAdapter


def build_document_content(
    paragraphs: list[str], title: str | None = "Title"
) -> DocumentContentDTO:
    full_text = " ".join(paragraphs)
    return DocumentContentDTO(
        word_count=len(full_text.split()),
        char_count=len(full_text),
        paragraph_count=len(paragraphs),
        title=title,
        paragraphs=paragraphs,
    )


def _certain_choice(answer: str) -> LayaChoiceDecisionDTO:
    return LayaChoiceDecisionDTO(answer=answer, probabilities={answer: 1.0}, confidence=1.0)


def build_laya_decision(
    clarity: float,
    coherence: float,
    argumentation: float,
    conclusions: float,
    editorial_verdict: str = LayaEditorialVerdict.SUSTAINED.value,
    research_line: str = "1",
) -> LayaDecisionResultDTO:
    return replace(
        DEFAULT_DECISION_RESULT,
        editorial_verdict=_certain_choice(editorial_verdict),
        research_line=_certain_choice(research_line),
        score_clarity=LayaScoreDecisionDTO(expected_value=clarity, confidence=1.0),
        score_coherence=LayaScoreDecisionDTO(expected_value=coherence, confidence=1.0),
        score_argumentation=LayaScoreDecisionDTO(expected_value=argumentation, confidence=1.0),
        score_conclusions=LayaScoreDecisionDTO(expected_value=conclusions, confidence=1.0),
    )


CLARITY_COHERENCE_PROMPT_TEMPLATE = """Eres un revisor editorial académico experto.

TEXTO A ANALIZAR:
{text_sample}

Evalúa Claridad y Coherencia."""

ARGUMENTATION_CONCLUSIONS_PROMPT_TEMPLATE = """Eres un revisor editorial académico experto.

TEXTO A ANALIZAR:
{text_sample}

Evalúa Argumentación y Conclusiones."""


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


def build_analyzer(fake_adapter: FakeLlmGeneratorAdapter) -> QualityAnalyzer:
    suitability_adapter = FakeLlmGeneratorAdapter(
        [SUITABILITY_CONTRIBUTION_RESPONSE, SUITABILITY_ALIGNMENT_RESPONSE]
    )
    editorial_suitability_analyzer = EditorialSuitabilityAnalyzer(
        llm_generator=suitability_adapter,
        parser=EditorialSuitabilityParser(),
        contribution_prompt_template=SUITABILITY_CONTRIBUTION_PROMPT_TEMPLATE,
        alignment_prompt_template=SUITABILITY_ALIGNMENT_PROMPT_TEMPLATE,
        research_lines=SUITABILITY_RESEARCH_LINES,
    )
    return QualityAnalyzer(
        llm_generator=fake_adapter,
        text_sampler=QualityTextSampler(),
        response_parser=QualityResponseParser(),
        clarity_coherence_prompt_template=CLARITY_COHERENCE_PROMPT_TEMPLATE,
        argumentation_conclusions_prompt_template=ARGUMENTATION_CONCLUSIONS_PROMPT_TEMPLATE,
        editorial_suitability_analyzer=editorial_suitability_analyzer,
    )


ALL_GOOD_DECISION = build_laya_decision(
    clarity=8.0, coherence=7.0, argumentation=9.0, conclusions=7.5
)

LOW_CLARITY_RESPONSE = """**1. Claridad del argumento** [Puntuación: 2/10]
El argumento central es confuso y dificil de seguir en todo el texto.

**2. Coherencia** [Puntuación: 2/10]
Este feedback de coherencia no debe usarse porque Laya la considera buena.
"""

LOW_ARGUMENTATION_RESPONSE = """**1. Argumentación** [Puntuación: 2/10]
Los argumentos presentados son debiles y carecen de fundamento solido.

**2. Conclusiones** [Puntuación: 2/10]
Este feedback de conclusiones no debe usarse porque Laya las considera buenas.
"""


class TestQualityAnalyzer(TestCase):
    def setUp(self):
        self.document_content = build_document_content(["Parrafo uno.", "Parrafo dos."])

    def test_scores_come_from_laya_and_overall_score_is_their_mean(self):
        analyzer = build_analyzer(FakeLlmGeneratorAdapter([]))

        result = analyzer.analyze(self.document_content, ALL_GOOD_DECISION)

        self.assertEqual(result.dimension_scores["claridad"]["score"], 8.0)
        self.assertEqual(result.dimension_scores["coherencia"]["score"], 7.0)
        self.assertEqual(result.dimension_scores["argumentacion"]["score"], 9.0)
        self.assertEqual(result.dimension_scores["conclusiones"]["score"], 7.5)
        self.assertEqual(result.overall_score, 7.875)

    def test_overall_score_resolves_to_its_quality_level(self):
        analyzer = build_analyzer(FakeLlmGeneratorAdapter([]))

        result = analyzer.analyze(self.document_content, build_laya_decision(7, 7, 7, 7))

        self.assertEqual(result.quality_level, QualityLevel.GOOD)

    def test_no_llm_call_when_every_dimension_reaches_the_good_threshold(self):
        fake_adapter = FakeLlmGeneratorAdapter([])
        analyzer = build_analyzer(fake_adapter)

        result = analyzer.analyze(self.document_content, ALL_GOOD_DECISION)

        self.assertEqual(fake_adapter.call_count, 0)
        for dimension_data in result.dimension_scores.values():
            self.assertEqual(dimension_data["feedback"], "")

    def test_low_clarity_requests_only_the_clarity_coherence_prompt(self):
        fake_adapter = FakeLlmGeneratorAdapter([LOW_CLARITY_RESPONSE])
        analyzer = build_analyzer(fake_adapter)

        analyzer.analyze(self.document_content, build_laya_decision(4.0, 8.0, 8.0, 8.0))

        self.assertEqual(fake_adapter.call_count, 1)
        self.assertIn("Evalúa Claridad y Coherencia.", fake_adapter.received_prompts[0])

    def test_low_argumentation_requests_only_the_argumentation_conclusions_prompt(self):
        fake_adapter = FakeLlmGeneratorAdapter([LOW_ARGUMENTATION_RESPONSE])
        analyzer = build_analyzer(fake_adapter)

        analyzer.analyze(self.document_content, build_laya_decision(8.0, 8.0, 4.0, 8.0))

        self.assertEqual(fake_adapter.call_count, 1)
        self.assertIn("Evalúa Argumentación y Conclusiones.", fake_adapter.received_prompts[0])

    def test_all_dimensions_low_requests_both_prompts(self):
        fake_adapter = FakeLlmGeneratorAdapter([LOW_CLARITY_RESPONSE, LOW_ARGUMENTATION_RESPONSE])
        analyzer = build_analyzer(fake_adapter)

        analyzer.analyze(self.document_content, build_laya_decision(4.0, 4.0, 4.0, 4.0))

        self.assertEqual(fake_adapter.call_count, 2)

    def test_threshold_is_inclusive_so_a_score_of_seven_requests_no_feedback(self):
        fake_adapter = FakeLlmGeneratorAdapter([])
        analyzer = build_analyzer(fake_adapter)

        analyzer.analyze(self.document_content, build_laya_decision(7.0, 7.0, 7.0, 7.0))

        self.assertEqual(fake_adapter.call_count, 0)

    def test_feedback_is_kept_only_for_low_dimensions_and_scores_ignore_the_llm(self):
        fake_adapter = FakeLlmGeneratorAdapter([LOW_CLARITY_RESPONSE])
        analyzer = build_analyzer(fake_adapter)

        result = analyzer.analyze(self.document_content, build_laya_decision(4.0, 8.0, 8.0, 8.0))

        self.assertEqual(result.dimension_scores["claridad"]["score"], 4.0)
        self.assertIn("confuso", result.dimension_scores["claridad"]["feedback"])
        self.assertEqual(result.dimension_scores["coherencia"]["score"], 8.0)
        self.assertEqual(result.dimension_scores["coherencia"]["feedback"], "")
        self.assertEqual(result.dimension_scores["argumentacion"]["feedback"], "")

    def test_unusable_feedback_response_for_a_low_dimension_raises_quality_analysis_failed(self):
        fake_adapter = FakeLlmGeneratorAdapter(
            ["Este texto no contiene ningun encabezado de dimension reconocible."]
        )
        analyzer = build_analyzer(fake_adapter)

        with self.assertRaises(QualityAnalysisFailed):
            analyzer.analyze(self.document_content, build_laya_decision(4.0, 8.0, 8.0, 8.0))

    def test_domain_service_has_zero_infrastructure_imports(self):
        source = Path("src/domain/quality/quality_analyzer.py").read_text(encoding="utf-8")

        self.assertNotIn("src.infrastructure", source)
        self.assertNotIn("import ollama", source)
        self.assertNotIn("from ollama", source)

    def test_rendered_prompt_preserves_legacy_wording_with_sample_interpolated(self):
        fake_adapter = FakeLlmGeneratorAdapter([LOW_CLARITY_RESPONSE])
        analyzer = build_analyzer(fake_adapter)

        analyzer.analyze(self.document_content, build_laya_decision(4.0, 8.0, 8.0, 8.0))

        text_sample = QualityTextSampler().build_sample(self.document_content)
        self.assertIn(
            "Eres un revisor editorial académico experto.", fake_adapter.received_prompts[0]
        )
        self.assertIn(text_sample, fake_adapter.received_prompts[0])

    def test_result_includes_editorial_suitability_dto_from_analyzer(self):
        analyzer = build_analyzer(FakeLlmGeneratorAdapter([]))

        result = analyzer.analyze(self.document_content, ALL_GOOD_DECISION)

        suitability = result.editorial_suitability
        assert isinstance(suitability, EditorialSuitabilityDTO)
        self.assertEqual(suitability.contribution_verdict, "SUSTENTADA")
        self.assertEqual(suitability.alignment_verdict, "ALINEADO")

    def test_quality_analyzer_forwards_laya_decision_to_editorial_suitability_analyzer(self):
        analyzer = build_analyzer(FakeLlmGeneratorAdapter([]))

        positive_result = analyzer.analyze(self.document_content, ALL_GOOD_DECISION)
        assert positive_result.editorial_suitability is not None
        self.assertEqual(positive_result.editorial_suitability.contribution_verdict, "SUSTENTADA")

        negative_decision = build_laya_decision(
            8.0, 8.0, 8.0, 8.0, editorial_verdict=LayaEditorialVerdict.NOT_SUSTAINED.value
        )
        negative_result = analyzer.analyze(self.document_content, negative_decision)
        assert negative_result.editorial_suitability is not None
        self.assertEqual(
            negative_result.editorial_suitability.contribution_verdict, "NO SUSTENTADA"
        )

    def test_quality_analyzer_module_defines_exactly_one_class(self):
        source = Path("src/domain/quality/quality_analyzer.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        top_level_classes = [
            node.name for node in ast.iter_child_nodes(tree) if isinstance(node, ast.ClassDef)
        ]

        self.assertEqual(top_level_classes, ["QualityAnalyzer"])
