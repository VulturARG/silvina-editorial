from unittest import TestCase

from src.domain.quality.first_sentence_extractor import FirstSentenceExtractor
from src.domain.quality.suitability_field_truncator import SuitabilityFieldTruncator


class TestSuitabilityFieldTruncator(TestCase):
    def setUp(self) -> None:
        self.first_sentence_extractor = FirstSentenceExtractor()
        self.truncator = SuitabilityFieldTruncator(
            first_sentence_extractor=self.first_sentence_extractor
        )

    def test_truncate_returns_empty_text_when_input_is_empty(self) -> None:
        result = self.truncator.truncate("", 120)

        self.assertEqual(result, "")

    def test_truncate_returns_untouched_when_sentence_length_is_strictly_less_than_max(
        self,
    ) -> None:
        text = "a" * 119

        result = self.truncator.truncate(text, 120)

        self.assertEqual(result, "a" * 119)
        self.assertEqual(len(result), 119)

    def test_truncate_truncates_when_sentence_length_equals_max_length(self) -> None:
        text = "a" * 120

        result = self.truncator.truncate(text, 120)

        self.assertTrue(result.endswith("…"))
        self.assertLess(len(result), 120)
        self.assertEqual(result, ("a" * 118) + "…")

    def test_truncate_cuts_at_word_boundary_with_ellipsis(self) -> None:
        text = ("palabra " * 40) + "final."

        result = self.truncator.truncate(text, 120)

        self.assertTrue(result.endswith("…"))
        self.assertLess(len(result), 120)
        self.assertFalse(result.endswith("p…"))

    def test_truncate_removes_trailing_punctuation_before_ellipsis(self) -> None:
        text = "Primera parte de la oracion, con coma antes del corte. " + ("x" * 200)

        result = self.truncator.truncate(text, 35)

        self.assertFalse(result.endswith(",…"))
        self.assertFalse(result.endswith(" …"))
        self.assertTrue(result.endswith("…"))

    def test_truncate_uses_first_sentence_before_applying_length_limit(self) -> None:
        text = "Primera oracion corta. Segunda oracion muy larga que excede con creces cualquier limite posible."

        result = self.truncator.truncate(text, 120)

        self.assertEqual(result, "Primera oracion corta.")

    def test_truncate_handles_unbroken_string_without_spaces(self) -> None:
        text = "x" * 300

        result = self.truncator.truncate(text, 120)

        self.assertEqual(result, ("x" * 118) + "…")

    def test_repeated_and_interleaved_calls_produce_identical_results(self) -> None:
        sample_a = ("palabra " * 30) + "a."
        sample_b = ("otra " * 35) + "b."

        result_a_first = self.truncator.truncate(sample_a, 120)
        result_b_first = self.truncator.truncate(sample_b, 120)
        result_a_second = self.truncator.truncate(sample_a, 120)
        result_b_second = self.truncator.truncate(sample_b, 120)

        self.assertEqual(result_a_first, result_a_second)
        self.assertEqual(result_b_first, result_b_second)
