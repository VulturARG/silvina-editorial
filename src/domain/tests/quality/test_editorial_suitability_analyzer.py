from dataclasses import replace
from unittest import TestCase

from src.domain.dtos.editorial_suitability_dto import EditorialSuitabilityDTO
from src.domain.dtos.laya_choice_decision_dto import LayaChoiceDecisionDTO
from src.domain.dtos.laya_decision_result_dto import LayaDecisionResultDTO
from src.domain.enums.laya_editorial_verdict import LayaEditorialVerdict
from src.domain.enums.laya_research_line_answer import LayaResearchLineAnswer
from src.domain.quality.editorial_suitability_analyzer import EditorialSuitabilityAnalyzer
from src.domain.quality.editorial_suitability_parser import EditorialSuitabilityParser
from src.domain.tests.laya.fake_laya_decision_port import DEFAULT_DECISION_RESULT
from src.domain.tests.quality.fake_llm_generator_adapter import FakeLlmGeneratorAdapter

CONTRIBUTION_PROMPT_TEMPLATE = "Evalua contribucion.\nTEXTO:\n{text_sample}"
ALIGNMENT_PROMPT_TEMPLATE = "Evalua alineacion.\nLINEAS:\n{research_lines}\nTEXTO:\n{text_sample}"
RESEARCH_LINES_FIXTURE = (
    "1. Linea de prueba uno — descripcion de la linea uno\n"
    "2. Linea de prueba dos — descripcion de la linea dos"
)

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


def _certain_choice(answer: str) -> LayaChoiceDecisionDTO:
    return LayaChoiceDecisionDTO(answer=answer, probabilities={answer: 1.0}, confidence=1.0)


def build_decision(
    editorial_verdict: str = LayaEditorialVerdict.SUSTAINED.value,
    research_line: str = "1",
) -> LayaDecisionResultDTO:
    return replace(
        DEFAULT_DECISION_RESULT,
        editorial_verdict=_certain_choice(editorial_verdict),
        research_line=_certain_choice(research_line),
    )


def build_analyzer(fake_adapter: FakeLlmGeneratorAdapter) -> EditorialSuitabilityAnalyzer:
    return EditorialSuitabilityAnalyzer(
        llm_generator=fake_adapter,
        parser=EditorialSuitabilityParser(),
        contribution_prompt_template=CONTRIBUTION_PROMPT_TEMPLATE,
        alignment_prompt_template=ALIGNMENT_PROMPT_TEMPLATE,
        research_lines=RESEARCH_LINES_FIXTURE,
    )


class TestEditorialSuitabilityAnalyzer(TestCase):
    def test_positive_verdicts_make_zero_llm_calls_and_return_resolved_lines(self):
        fake_adapter = FakeLlmGeneratorAdapter([])
        analyzer = build_analyzer(fake_adapter)

        result = analyzer.analyze(
            text_sample="Texto de muestra del articulo.",
            laya_decision=build_decision(
                editorial_verdict=LayaEditorialVerdict.SUSTAINED.value, research_line="1"
            ),
        )

        self.assertEqual(fake_adapter.call_count, 0)
        self.assertIsInstance(result, EditorialSuitabilityDTO)
        self.assertEqual(result.contribution_verdict, "SUSTENTADA")
        self.assertEqual(result.contribution_phrase, "")
        self.assertEqual(result.contribution_observation, "Contribución sustentada.")
        self.assertEqual(result.alignment_verdict, "ALINEADO")
        self.assertEqual(result.alignment_lines, "1. Linea de prueba uno")
        self.assertEqual(result.alignment_justification, "")

    def test_partial_contribution_calls_llm_once_keeping_laya_verdict(self):
        fake_adapter = FakeLlmGeneratorAdapter([CONTRIBUTION_RESPONSE])
        analyzer = build_analyzer(fake_adapter)

        result = analyzer.analyze(
            text_sample="Texto de muestra del articulo.",
            laya_decision=build_decision(
                editorial_verdict=LayaEditorialVerdict.PARTIAL.value, research_line="1"
            ),
        )

        self.assertEqual(fake_adapter.call_count, 1)
        self.assertEqual(result.contribution_verdict, "PARCIAL")
        self.assertEqual(result.contribution_phrase, "Propone un marco de analisis original.")
        self.assertEqual(
            result.contribution_observation,
            "Contribución declarada pero no suficientemente sustentada.",
        )
        self.assertEqual(fake_adapter.received_options[0], {"temperature": 0.1, "num_predict": 300})
        self.assertIn("Texto de muestra del articulo.", fake_adapter.received_prompts[0])
        self.assertNotIn("{text_sample}", fake_adapter.received_prompts[0])

    def test_not_sustained_contribution_calls_llm_once_keeping_laya_verdict(self):
        fake_adapter = FakeLlmGeneratorAdapter([CONTRIBUTION_RESPONSE])
        analyzer = build_analyzer(fake_adapter)

        result = analyzer.analyze(
            text_sample="Texto de muestra del articulo.",
            laya_decision=build_decision(
                editorial_verdict=LayaEditorialVerdict.NOT_SUSTAINED.value, research_line="1"
            ),
        )

        self.assertEqual(fake_adapter.call_count, 1)
        self.assertEqual(result.contribution_verdict, "NO SUSTENTADA")
        self.assertEqual(result.contribution_phrase, "Propone un marco de analisis original.")
        self.assertEqual(result.contribution_observation, "Sin contribución observada o declarada.")

    def test_none_research_line_calls_llm_once_forcing_not_aligned_verdict(self):
        fake_adapter = FakeLlmGeneratorAdapter([ALIGNMENT_RESPONSE])
        analyzer = build_analyzer(fake_adapter)

        result = analyzer.analyze(
            text_sample="Texto de muestra del articulo.",
            laya_decision=build_decision(
                editorial_verdict=LayaEditorialVerdict.SUSTAINED.value,
                research_line=LayaResearchLineAnswer.NONE.value,
            ),
        )

        self.assertEqual(fake_adapter.call_count, 1)
        self.assertEqual(result.alignment_verdict, "NO ALINEADO")
        self.assertEqual(result.alignment_lines, "Linea 1 y 2.")
        self.assertEqual(
            result.alignment_justification,
            "Se relaciona directamente con las lineas mencionadas.",
        )
        self.assertEqual(fake_adapter.received_options[0], {"temperature": 0.1, "num_predict": 300})
        alignment_prompt = fake_adapter.received_prompts[0]
        self.assertIn("Texto de muestra del articulo.", alignment_prompt)
        self.assertNotIn("{text_sample}", alignment_prompt)
        self.assertNotIn("{research_lines}", alignment_prompt)
        self.assertIn(RESEARCH_LINES_FIXTURE, alignment_prompt)

    def test_both_negative_calls_llm_twice_in_order_contribution_then_alignment(self):
        fake_adapter = FakeLlmGeneratorAdapter([CONTRIBUTION_RESPONSE, ALIGNMENT_RESPONSE])
        analyzer = build_analyzer(fake_adapter)

        result = analyzer.analyze(
            text_sample="Texto de muestra del articulo.",
            laya_decision=build_decision(
                editorial_verdict=LayaEditorialVerdict.NOT_SUSTAINED.value,
                research_line=LayaResearchLineAnswer.NONE.value,
            ),
        )

        self.assertEqual(fake_adapter.call_count, 2)
        self.assertIn("Evalua contribucion.", fake_adapter.received_prompts[0])
        self.assertIn("Evalua alineacion.", fake_adapter.received_prompts[1])
        self.assertEqual(fake_adapter.received_options[0], {"temperature": 0.1, "num_predict": 300})
        self.assertEqual(fake_adapter.received_options[1], {"temperature": 0.1, "num_predict": 300})
        self.assertEqual(result.contribution_verdict, "NO SUSTENTADA")
        self.assertEqual(result.contribution_phrase, "Propone un marco de analisis original.")
        self.assertEqual(result.contribution_observation, "Sin contribución observada o declarada.")
        self.assertEqual(result.alignment_verdict, "NO ALINEADO")
        self.assertEqual(result.alignment_lines, "Linea 1 y 2.")
        self.assertEqual(
            result.alignment_justification,
            "Se relaciona directamente con las lineas mencionadas.",
        )

    def test_research_line_not_found_in_fixture_falls_back_to_raw_id(self):
        fake_adapter = FakeLlmGeneratorAdapter([])
        analyzer = build_analyzer(fake_adapter)

        result = analyzer.analyze(
            text_sample="Texto de muestra del articulo.",
            laya_decision=build_decision(
                editorial_verdict=LayaEditorialVerdict.SUSTAINED.value, research_line="99"
            ),
        )

        self.assertEqual(fake_adapter.call_count, 0)
        self.assertEqual(result.alignment_verdict, "ALINEADO")
        self.assertEqual(result.alignment_lines, "99")
        self.assertEqual(result.alignment_justification, "")

    def test_custom_generation_options_are_passed_to_llm_generator(self):
        fake_adapter = FakeLlmGeneratorAdapter([CONTRIBUTION_RESPONSE])
        custom_options = {"temperature": 0.5, "num_predict": 150}
        analyzer = EditorialSuitabilityAnalyzer(
            llm_generator=fake_adapter,
            parser=EditorialSuitabilityParser(),
            contribution_prompt_template=CONTRIBUTION_PROMPT_TEMPLATE,
            alignment_prompt_template=ALIGNMENT_PROMPT_TEMPLATE,
            research_lines=RESEARCH_LINES_FIXTURE,
            generation_options=custom_options,
        )

        analyzer.analyze(
            text_sample="Texto de muestra del articulo.",
            laya_decision=build_decision(
                editorial_verdict=LayaEditorialVerdict.PARTIAL.value, research_line="1"
            ),
        )

        self.assertEqual(fake_adapter.received_options[0], custom_options)
