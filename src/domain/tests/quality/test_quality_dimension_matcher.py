from unittest import TestCase

from src.domain.enums.quality_dimension import QualityDimension
from src.domain.quality.quality_dimension_matcher import QualityDimensionMatcher


class TestQualityDimensionMatcher(TestCase):
    def test_matches_argumentation_from_keyword(self):
        matcher = QualityDimensionMatcher()
        block = "**1. Argumentación** [Puntuación: 8/10]\nTexto descriptivo."

        result = matcher.match(block)

        self.assertEqual(result, QualityDimension.ARGUMENTATION)

    def test_matches_conclusions_from_keyword(self):
        matcher = QualityDimensionMatcher()
        block = "**Conclusiones** [Puntuación: 9/10]\nTexto descriptivo."

        result = matcher.match(block)

        self.assertEqual(result, QualityDimension.CONCLUSIONS)

    def test_matches_coherence_from_keyword(self):
        matcher = QualityDimensionMatcher()
        block = "**Coherencia** [Puntuación: 7/10]\nTexto descriptivo."

        result = matcher.match(block)

        self.assertEqual(result, QualityDimension.COHERENCE)

    def test_matches_clarity_from_keyword(self):
        matcher = QualityDimensionMatcher()
        block = "**Claridad** [Puntuación: 6/10]\nTexto descriptivo."

        result = matcher.match(block)

        self.assertEqual(result, QualityDimension.CLARITY)

    def test_argumento_keyword_resolves_to_clarity_not_argumentation(self):
        matcher = QualityDimensionMatcher()
        block = "**El argumento principal** [Puntuación: 7/10]\nTexto descriptivo."

        result = matcher.match(block)

        self.assertEqual(result, QualityDimension.CLARITY)

    def test_argumentation_takes_precedence_over_clarity_when_both_present(self):
        matcher = QualityDimensionMatcher()
        block = "**Argumentación y claridad** [Puntuación: 8/10]\nTexto descriptivo."

        result = matcher.match(block)

        self.assertEqual(result, QualityDimension.ARGUMENTATION)

    def test_conclusions_takes_precedence_over_clarity_when_both_present(self):
        matcher = QualityDimensionMatcher()
        block = "**Conclusiones sobre claridad** [Puntuación: 8/10]\nTexto descriptivo."

        result = matcher.match(block)

        self.assertEqual(result, QualityDimension.CONCLUSIONS)

    def test_keyword_after_character_inspection_limit_is_not_matched(self):
        matcher = QualityDimensionMatcher()
        padding = "x" * 200
        block = f"{padding}claridad en el texto"

        result = matcher.match(block)

        self.assertIsNone(result)

    def test_keyword_within_character_inspection_limit_is_matched(self):
        matcher = QualityDimensionMatcher()
        padding = "x" * 190
        block = f"{padding}claridad"

        result = matcher.match(block)

        self.assertEqual(result, QualityDimension.CLARITY)

    def test_returns_none_when_no_dimension_keyword_present(self):
        matcher = QualityDimensionMatcher()
        block = "Texto general sin dimensiones especificadas en esta seccion."

        result = matcher.match(block)

        self.assertIsNone(result)

    def test_returns_none_for_empty_block(self):
        matcher = QualityDimensionMatcher()

        result = matcher.match("")

        self.assertIsNone(result)
