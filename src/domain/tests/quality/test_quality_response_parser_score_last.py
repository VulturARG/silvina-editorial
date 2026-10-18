from unittest import TestCase

from src.domain.enums.quality_dimension import QualityDimension
from src.domain.tests.quality.quality_response_parser_builder_for_test import (
    QualityResponseParserBuilderForTest,
)


class TestQualityResponseParserScoreLast(TestCase):
    def test_score_last_layout_uses_final_score_line_instead_of_inline_mention(self):
        response = """### 1. Claridad del argumento
El argumento se sostiene, aunque la evidencia empírica merece 5/10 en la sección central.
Puntuación: 8/10

### 2. Coherencia
Las ideas se conectan lógicamente entre las distintas secciones del texto.
Puntuación: 6/10
"""
        parser = QualityResponseParserBuilderForTest().build()

        result = parser.parse(response)

        self.assertEqual(result.scores[QualityDimension.CLARITY].score, 8.0)
        self.assertEqual(result.scores[QualityDimension.COHERENCE].score, 6.0)

    def test_score_last_layout_keeps_score_line_out_of_feedback(self):
        response = """### 1. Claridad del argumento
El argumento se sostiene, aunque la evidencia empírica merece 5/10 en la sección central.
Puntuación: 8/10

### 2. Coherencia
Las ideas se conectan lógicamente entre las distintas secciones del texto.
Puntuación: 6/10
"""
        parser = QualityResponseParserBuilderForTest().build()

        result = parser.parse(response)

        clarity_feedback = result.scores[QualityDimension.CLARITY].feedback
        coherence_feedback = result.scores[QualityDimension.COHERENCE].feedback
        self.assertIn("merece 5/10 en la sección central", clarity_feedback)
        self.assertNotIn("Puntuación", clarity_feedback)
        self.assertNotIn("8/10", clarity_feedback)
        self.assertIn("Las ideas se conectan lógicamente", coherence_feedback)
        self.assertNotIn("Puntuación", coherence_feedback)
        self.assertNotIn("6/10", coherence_feedback)

    def test_header_score_wins_over_stray_trailing_score_line_in_original_layout(self):
        response = """**1. Claridad del argumento** [Puntuación: 8/10]
El argumento se sostiene con evidencia suficiente en el desarrollo general.
Puntuación: 3/10
"""
        parser = QualityResponseParserBuilderForTest().build()

        result = parser.parse(response)

        clarity = result.scores[QualityDimension.CLARITY]
        self.assertEqual(clarity.score, 8.0)
        self.assertIn("El argumento se sostiene con evidencia suficiente", clarity.feedback)
        self.assertIn("Puntuación: 3/10", clarity.feedback)
