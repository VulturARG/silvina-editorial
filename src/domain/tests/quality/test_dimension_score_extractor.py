from unittest import TestCase

from src.domain.dtos.dimension_score_dto import DimensionScoreDTO
from src.domain.quality.dimension_score_extractor import DimensionScoreExtractor


class TestDimensionScoreExtractor(TestCase):
    def setUp(self):
        self._unscored_dimension = DimensionScoreDTO(
            score=7.0,
            feedback="No disponible",
            feedback_blocks=(),
        )
        self._extractor = DimensionScoreExtractor(unscored_dimension=self._unscored_dimension)

    def test_extracts_explicit_score_bracket_format(self):
        block = "**1. Claridad** [Puntuación: 8.5/10]\nTexto descriptivo."

        result = self._extractor.extract(block)

        self.assertEqual(result, 8.5)

    def test_extracts_explicit_score_bracket_format_without_slash_ten(self):
        block = "**1. Claridad** [Puntuación: 8]\nTexto descriptivo."

        result = self._extractor.extract(block)

        self.assertEqual(result, 8.0)

    def test_extracts_explicit_score_slash_format(self):
        block = "**1. Claridad**\nCalificación: 9 / 10 puntos en la evaluacion."

        result = self._extractor.extract(block)

        self.assertEqual(result, 9.0)

    def test_clamps_score_above_maximum_to_ten(self):
        block = "**1. Claridad** [Puntuación: 15/10]\nTexto descriptivo."

        result = self._extractor.extract(block)

        self.assertEqual(result, 10.0)

    def test_infers_eight_point_five_for_excelente_narrative_keyword(self):
        block = "**1. Claridad**\nEl texto es excelente en su exposicion."

        result = self._extractor.extract(block)

        self.assertEqual(result, 8.5)

    def test_infers_eight_point_five_for_sobresaliente_narrative_keyword(self):
        block = "**1. Claridad**\nEl desarrollo es sobresaliente."

        result = self._extractor.extract(block)

        self.assertEqual(result, 8.5)

    def test_infers_eight_point_five_for_muy_bueno_narrative_keyword(self):
        block = "**1. Claridad**\nEl desempeno es muy bueno."

        result = self._extractor.extract(block)

        self.assertEqual(result, 8.5)

    def test_infers_seven_point_five_for_bueno_narrative_keyword(self):
        block = "**1. Claridad**\nEl argumento es bueno en general."

        result = self._extractor.extract(block)

        self.assertEqual(result, 7.5)

    def test_infers_seven_point_five_for_adecuado_narrative_keyword(self):
        block = "**1. Claridad**\nEl contenido es adecuado para el proposito."

        result = self._extractor.extract(block)

        self.assertEqual(result, 7.5)

    def test_infers_seven_point_five_for_correcto_narrative_keyword(self):
        block = "**1. Claridad**\nEl formato es correcto."

        result = self._extractor.extract(block)

        self.assertEqual(result, 7.5)

    def test_infers_six_point_zero_for_aceptable_narrative_keyword(self):
        block = "**1. Claridad**\nEl nivel resulta aceptable."

        result = self._extractor.extract(block)

        self.assertEqual(result, 6.0)

    def test_infers_six_point_zero_for_suficiente_narrative_keyword(self):
        block = "**1. Claridad**\nLa evidencia es suficiente pero basica."

        result = self._extractor.extract(block)

        self.assertEqual(result, 6.0)

    def test_infers_six_point_zero_for_regular_narrative_keyword(self):
        block = "**1. Claridad**\nLa coherencia es regular en esta seccion."

        result = self._extractor.extract(block)

        self.assertEqual(result, 6.0)

    def test_infers_four_point_zero_for_deficiente_narrative_keyword(self):
        block = "**1. Claridad**\nLa exposicion es deficiente."

        result = self._extractor.extract(block)

        self.assertEqual(result, 4.0)

    def test_infers_four_point_zero_for_debil_narrative_keyword(self):
        block = "**1. Claridad**\nEl analisis es débil y carece de sustento."

        result = self._extractor.extract(block)

        self.assertEqual(result, 4.0)

    def test_unaccented_debil_does_not_match_and_falls_back(self):
        block = "**1. Claridad**\nEl analisis es debil y carece de sustento."

        result = self._extractor.extract(block)

        self.assertEqual(result, 7.0)

    def test_infers_four_point_zero_for_pobre_narrative_keyword(self):
        block = "**1. Claridad**\nEl vocabulario es pobre."

        result = self._extractor.extract(block)

        self.assertEqual(result, 4.0)

    def test_insuficiente_contains_suficiente_and_resolves_to_six_due_to_ladder_order(self):
        block = "**1. Claridad**\nLa justificacion resulta insuficiente."

        result = self._extractor.extract(block)

        self.assertEqual(result, 6.0)

    def test_narrative_ladder_precedence_favors_higher_tier(self):
        block = "**1. Claridad**\nEl trabajo es excelente pero deficiente en partes."

        result = self._extractor.extract(block)

        self.assertEqual(result, 8.5)

    def test_falls_back_to_unscored_dimension_score_when_no_match(self):
        block = "**1. Claridad**\nTexto neutro sin indicadores de puntuacion."

        result = self._extractor.extract(block)

        self.assertEqual(result, 7.0)

    def test_falls_back_to_custom_unscored_dimension_score(self):
        custom_unscored = DimensionScoreDTO(
            score=5.5,
            feedback="Sin calificar",
            feedback_blocks=(),
        )
        extractor = DimensionScoreExtractor(unscored_dimension=custom_unscored)
        block = "**1. Claridad**\nTexto neutro sin indicadores."

        result = extractor.extract(block)

        self.assertEqual(result, 5.5)
