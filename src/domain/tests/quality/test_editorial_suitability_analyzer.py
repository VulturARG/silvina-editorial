from unittest import TestCase

from src.domain.dtos.editorial_suitability_dto import EditorialSuitabilityDTO
from src.domain.quality.editorial_suitability_analyzer import EditorialSuitabilityAnalyzer
from src.domain.tests.quality.editorial_suitability_parser_builder_for_test import (
    EditorialSuitabilityParserBuilderForTest,
)
from src.domain.tests.quality.fake_llm_generator_adapter import FakeLlmGeneratorAdapter

CONTRIBUTION_PROMPT_TEMPLATE = "Evalua contribucion.\nTEXTO:\n{text_sample}"
ALIGNMENT_PROMPT_TEMPLATE = "Evalua alineacion.\nLINEAS:\n{research_lines}\nTEXTO:\n{text_sample}"
RESEARCH_LINES_FIXTURE = "1. Linea de prueba uno\n2. Linea de prueba dos"

CONTRIBUTION_RESPONSE = (
    "VEREDICTO: SUSTENTADA\n"
    "CONTRIBUCION: Propone un marco de analisis original.\n"
    "OBSERVACION: sera ignorada.\n"
)
ALIGNMENT_RESPONSE = (
    "VEREDICTO: ALINEADO\n"
    "LINEAS: Linea 1 y 2.\n"
    "JUSTIFICACION: Se relaciona directamente con las lineas mencionadas.\n"
)


def build_analyzer(
    fake_adapter: FakeLlmGeneratorAdapter, temperature: float = 0.1, num_predict: int = 300
) -> EditorialSuitabilityAnalyzer:
    return EditorialSuitabilityAnalyzer(
        llm_generator=fake_adapter,
        parser=EditorialSuitabilityParserBuilderForTest().build(),
        contribution_prompt_template=CONTRIBUTION_PROMPT_TEMPLATE,
        alignment_prompt_template=ALIGNMENT_PROMPT_TEMPLATE,
        research_lines=RESEARCH_LINES_FIXTURE,
        temperature=temperature,
        num_predict=num_predict,
    )


class TestEditorialSuitabilityAnalyzer(TestCase):
    def test_generate_is_called_exactly_twice(self):
        fake_adapter = FakeLlmGeneratorAdapter([CONTRIBUTION_RESPONSE, ALIGNMENT_RESPONSE])
        analyzer = build_analyzer(fake_adapter)

        analyzer.analyze(text_sample="Texto de muestra del articulo.")

        self.assertEqual(fake_adapter.call_count, 2)

    def test_both_calls_use_temperature_and_num_predict_options(self):
        fake_adapter = FakeLlmGeneratorAdapter([CONTRIBUTION_RESPONSE, ALIGNMENT_RESPONSE])
        analyzer = build_analyzer(fake_adapter)

        analyzer.analyze(text_sample="Texto de muestra del articulo.")

        self.assertEqual(fake_adapter.received_options[0], {"temperature": 0.1, "num_predict": 300})
        self.assertEqual(fake_adapter.received_options[1], {"temperature": 0.1, "num_predict": 300})

    def test_both_calls_use_injected_temperature_and_num_predict_options(self):
        fake_adapter = FakeLlmGeneratorAdapter([CONTRIBUTION_RESPONSE, ALIGNMENT_RESPONSE])
        analyzer = build_analyzer(fake_adapter, temperature=0.6, num_predict=450)

        analyzer.analyze(text_sample="Texto de muestra del articulo.")

        expected_options = {"temperature": 0.6, "num_predict": 450}
        self.assertEqual(fake_adapter.received_options[0], expected_options)
        self.assertEqual(fake_adapter.received_options[1], expected_options)

    def test_constructor_without_temperature_or_num_predict_raises_type_error(self):
        fake_adapter = FakeLlmGeneratorAdapter([CONTRIBUTION_RESPONSE, ALIGNMENT_RESPONSE])
        incomplete_arguments = {
            "llm_generator": fake_adapter,
            "parser": EditorialSuitabilityParserBuilderForTest().build(),
            "contribution_prompt_template": CONTRIBUTION_PROMPT_TEMPLATE,
            "alignment_prompt_template": ALIGNMENT_PROMPT_TEMPLATE,
            "research_lines": RESEARCH_LINES_FIXTURE,
        }

        with self.assertRaises(TypeError):
            EditorialSuitabilityAnalyzer(**incomplete_arguments)

    def test_contribution_prompt_interpolates_text_sample(self):
        fake_adapter = FakeLlmGeneratorAdapter([CONTRIBUTION_RESPONSE, ALIGNMENT_RESPONSE])
        analyzer = build_analyzer(fake_adapter)

        analyzer.analyze(text_sample="Texto de muestra del articulo.")

        self.assertIn("Texto de muestra del articulo.", fake_adapter.received_prompts[0])
        self.assertNotIn("{text_sample}", fake_adapter.received_prompts[0])

    def test_alignment_prompt_interpolates_text_sample_and_research_lines(self):
        fake_adapter = FakeLlmGeneratorAdapter([CONTRIBUTION_RESPONSE, ALIGNMENT_RESPONSE])
        analyzer = build_analyzer(fake_adapter)

        analyzer.analyze(text_sample="Texto de muestra del articulo.")

        alignment_prompt = fake_adapter.received_prompts[1]
        self.assertIn("Texto de muestra del articulo.", alignment_prompt)
        self.assertNotIn("{text_sample}", alignment_prompt)
        self.assertNotIn("{research_lines}", alignment_prompt)
        self.assertIn(RESEARCH_LINES_FIXTURE, alignment_prompt)

    def test_analyze_returns_editorial_suitability_dto_combining_both_parses(self):
        fake_adapter = FakeLlmGeneratorAdapter([CONTRIBUTION_RESPONSE, ALIGNMENT_RESPONSE])
        analyzer = build_analyzer(fake_adapter)

        result = analyzer.analyze(text_sample="Texto de muestra del articulo.")

        self.assertIsInstance(result, EditorialSuitabilityDTO)
        self.assertEqual(result.contribution_verdict, "SUSTENTADA")
        self.assertEqual(result.contribution_phrase, "Propone un marco de analisis original.")
        self.assertEqual(
            result.contribution_observation,
            "Contribución sustentada — Propone un marco de analisis original.",
        )
        self.assertEqual(result.alignment_verdict, "ALINEADO")
        self.assertEqual(result.alignment_lines, "Linea 1 y 2.")
        self.assertEqual(
            result.alignment_justification,
            "Se relaciona directamente con las lineas mencionadas.",
        )
