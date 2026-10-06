from unittest import TestCase

from src.domain.enums.contribution_verdict import ContributionVerdict
from src.domain.quality.contribution_observation_builder import ContributionObservationBuilder
from src.domain.quality.first_sentence_extractor import FirstSentenceExtractor
from src.domain.quality.suitability_field_truncator import SuitabilityFieldTruncator


class TestContributionObservationBuilder(TestCase):
    def setUp(self) -> None:
        first_sentence_extractor = FirstSentenceExtractor()
        self.truncator = SuitabilityFieldTruncator(
            first_sentence_extractor=first_sentence_extractor
        )
        self.builder = ContributionObservationBuilder(
            field_truncator=self.truncator,
            max_length=120,
        )

    def test_build_observation_for_not_supported_returns_fixed_observation(self) -> None:
        result = self.builder.build_observation(
            verdict=ContributionVerdict.NOT_SUPPORTED,
            phrase="Cualquier frase proporcionada.",
        )

        self.assertEqual(result, "Sin contribución observada o declarada.")

    def test_build_observation_for_partial_returns_fixed_observation(self) -> None:
        result = self.builder.build_observation(
            verdict=ContributionVerdict.PARTIAL,
            phrase="Cualquier frase proporcionada.",
        )

        self.assertEqual(result, "Contribución declarada pero no suficientemente sustentada.")

    def test_build_observation_for_supported_without_phrase_returns_fallback(self) -> None:
        result = self.builder.build_observation(
            verdict=ContributionVerdict.SUPPORTED,
            phrase="",
        )

        self.assertEqual(result, "Contribución sustentada.")

    def test_build_observation_for_supported_with_short_phrase_formats_message(self) -> None:
        phrase = "Aporte novedoso a la doctrina."

        result = self.builder.build_observation(
            verdict=ContributionVerdict.SUPPORTED,
            phrase=phrase,
        )

        self.assertEqual(result, f"Contribución sustentada — {phrase}")

    def test_build_observation_for_supported_with_long_phrase_truncates_at_max_length(self) -> None:
        phrase = "palabra " * 30

        result = self.builder.build_observation(
            verdict=ContributionVerdict.SUPPORTED,
            phrase=phrase,
        )

        self.assertTrue(result.startswith("Contribución sustentada — palabra "))
        self.assertTrue(result.endswith("…"))
        self.assertLess(len(result), 120)

    def test_build_observation_respects_custom_max_length(self) -> None:
        builder = ContributionObservationBuilder(
            field_truncator=self.truncator,
            max_length=50,
        )
        phrase = "Aporte muy extenso para el limite corto configurado."

        result = builder.build_observation(
            verdict=ContributionVerdict.SUPPORTED,
            phrase=phrase,
        )

        self.assertLess(len(result), 50)
        self.assertTrue(result.endswith("…"))

    def test_repeated_and_interleaved_calls_produce_identical_results(self) -> None:
        result_supported_first = self.builder.build_observation(
            ContributionVerdict.SUPPORTED, "Frase A."
        )
        result_partial_first = self.builder.build_observation(
            ContributionVerdict.PARTIAL, "Frase B."
        )
        result_supported_second = self.builder.build_observation(
            ContributionVerdict.SUPPORTED, "Frase A."
        )
        result_partial_second = self.builder.build_observation(
            ContributionVerdict.PARTIAL, "Frase B."
        )

        self.assertEqual(result_supported_first, result_supported_second)
        self.assertEqual(result_partial_first, result_partial_second)
