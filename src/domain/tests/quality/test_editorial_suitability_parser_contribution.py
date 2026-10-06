from unittest import TestCase

from src.domain.enums.contribution_verdict import ContributionVerdict
from src.domain.tests.quality.editorial_suitability_parser_builder_for_test import (
    EditorialSuitabilityParserBuilderForTest,
)


class TestEditorialSuitabilityParserContribution(TestCase):
    def setUp(self) -> None:
        self.parser = EditorialSuitabilityParserBuilderForTest().build()

    def test_case_insensitive_labels_are_recognized(self) -> None:
        raw = (
            "veredicto: sustentada\n"
            "contribucion: Aporta un marco novedoso para el análisis operativo.\n"
            "observacion: Sera ignorada porque el veredicto es sustentada.\n"
        )

        assessment = self.parser.parse_contribution(raw)

        self.assertEqual(assessment.verdict, ContributionVerdict.SUPPORTED)
        self.assertEqual(assessment.phrase, "Aporta un marco novedoso para el análisis operativo.")
        self.assertEqual(
            assessment.observation,
            "Contribución sustentada — Aporta un marco novedoso para el análisis operativo.",
        )

    def test_no_sustentada_verdict_sets_fixed_observation(self) -> None:
        raw = "VEREDICTO: NO SUSTENTADA\nOBSERVACION: Esto debe ser ignorado por completo.\n"

        assessment = self.parser.parse_contribution(raw)

        self.assertEqual(assessment.verdict, ContributionVerdict.NOT_SUPPORTED)
        self.assertEqual(assessment.observation, "Sin contribución observada o declarada.")

    def test_parcial_verdict_sets_fixed_observation(self) -> None:
        raw = (
            "VEREDICTO: PARCIAL\n"
            "CONTRIBUCION: Se menciona un aporte pero sin desarrollo suficiente.\n"
        )

        assessment = self.parser.parse_contribution(raw)

        self.assertEqual(assessment.verdict, ContributionVerdict.PARTIAL)
        self.assertEqual(
            assessment.observation, "Contribución declarada pero no suficientemente sustentada."
        )

    def test_sustentada_without_phrase_uses_fallback_observation(self) -> None:
        raw = "VEREDICTO: SUSTENTADA\n"

        assessment = self.parser.parse_contribution(raw)

        self.assertEqual(assessment.verdict, ContributionVerdict.SUPPORTED)
        self.assertEqual(assessment.phrase, "")
        self.assertEqual(assessment.observation, "Contribución sustentada.")

    def test_bold_label_with_colon_inside_bold_is_parsed_without_markdown(self) -> None:
        raw = (
            "**VEREDICTO:** SUSTENTADA\n"
            "**CONTRIBUCION:** Síntesis y taxonomía de tres hipótesis sobre razonamiento emergente.\n"
        )

        assessment = self.parser.parse_contribution(raw)

        self.assertEqual(assessment.verdict, ContributionVerdict.SUPPORTED)
        self.assertEqual(
            assessment.phrase,
            "Síntesis y taxonomía de tres hipótesis sobre razonamiento emergente.",
        )
        self.assertFalse(assessment.phrase.startswith("*"))
        self.assertFalse(assessment.phrase.startswith(":"))
        self.assertFalse(assessment.phrase.startswith(" "))
        self.assertNotIn("**", assessment.phrase)
        self.assertEqual(
            assessment.observation,
            "Contribución sustentada — Síntesis y taxonomía de tres hipótesis sobre razonamiento emergente.",
        )

    def test_bold_label_with_colon_outside_bold_is_parsed_without_markdown(self) -> None:
        raw = (
            "**VEREDICTO**: SUSTENTADA\n"
            "**CONTRIBUCION**: Síntesis y taxonomía de tres hipótesis sobre razonamiento emergente.\n"
        )

        assessment = self.parser.parse_contribution(raw)

        self.assertEqual(assessment.verdict, ContributionVerdict.SUPPORTED)
        self.assertEqual(
            assessment.phrase,
            "Síntesis y taxonomía de tres hipótesis sobre razonamiento emergente.",
        )
        self.assertFalse(assessment.phrase.startswith("*"))
        self.assertFalse(assessment.phrase.startswith(":"))
        self.assertFalse(assessment.phrase.startswith(" "))
        self.assertNotIn("**", assessment.phrase)
        self.assertEqual(
            assessment.observation,
            "Contribución sustentada — Síntesis y taxonomía de tres hipótesis sobre razonamiento emergente.",
        )

    def test_plain_label_is_parsed_without_markdown(self) -> None:
        raw = (
            "VEREDICTO: SUSTENTADA\n"
            "CONTRIBUCION: Síntesis y taxonomía de tres hipótesis sobre razonamiento emergente.\n"
        )

        assessment = self.parser.parse_contribution(raw)

        self.assertEqual(assessment.verdict, ContributionVerdict.SUPPORTED)
        self.assertEqual(
            assessment.phrase,
            "Síntesis y taxonomía de tres hipótesis sobre razonamiento emergente.",
        )
        self.assertFalse(assessment.phrase.startswith("*"))
        self.assertFalse(assessment.phrase.startswith(":"))
        self.assertFalse(assessment.phrase.startswith(" "))
        self.assertNotIn("**", assessment.phrase)

    def test_paired_bold_in_middle_of_contribution_phrase_is_stripped(self) -> None:
        raw = (
            "VEREDICTO: SUSTENTADA\n"
            "CONTRIBUCION: Propone la **síntesis** de tres hipótesis novedosas.\n"
        )

        assessment = self.parser.parse_contribution(raw)

        self.assertEqual(assessment.verdict, ContributionVerdict.SUPPORTED)
        self.assertEqual(
            assessment.phrase,
            "Propone la síntesis de tres hipótesis novedosas.",
        )
        self.assertNotIn("**", assessment.phrase)
        self.assertEqual(
            assessment.observation,
            "Contribución sustentada — Propone la síntesis de tres hipótesis novedosas.",
        )
