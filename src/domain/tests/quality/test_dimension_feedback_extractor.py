from unittest import TestCase

from src.domain.dtos.dimension_score_dto import DimensionScoreDTO
from src.domain.enums.feedback_block_kind import FeedbackBlockKind
from src.domain.quality.dimension_feedback_extractor import DimensionFeedbackExtractor
from src.domain.tests.quality.feedback_structure_parser_builder_for_test import (
    FeedbackStructureParserBuilderForTest,
)


class TestDimensionFeedbackExtractor(TestCase):
    def setUp(self):
        self._unscored_dimension = DimensionScoreDTO(
            score=7.0,
            feedback="No disponible",
            feedback_blocks=(),
        )
        self._structure_parser = FeedbackStructureParserBuilderForTest().build()
        self._extractor = DimensionFeedbackExtractor(
            feedback_structure_parser=self._structure_parser,
            unscored_dimension=self._unscored_dimension,
        )

    def test_extracts_feedback_text_and_blocks_for_valid_block(self):
        block = """## **1. Claridad** [Puntuación: 8/10]
**Fortalezas:**
- Presenta una estructura argumentativa sólida y bien definida.
"""

        result = self._extractor.extract(block)

        self.assertIn("Fortalezas:", result.feedback)
        self.assertIn("Presenta una estructura argumentativa", result.feedback)
        self.assertGreater(len(result.blocks), 0)

    def test_removes_recommendation_tail_from_block(self):
        block = """## **1. Claridad** [Puntuación: 8/10]
**Fortalezas:**
- Presenta ideas muy claras y desarrolladas adecuadamente.

**RECOMENDACIÓN GENERAL:**
- Esta recomendacion debe ser eliminada por completo.
"""

        result = self._extractor.extract(block)

        self.assertNotIn("RECOMENDACIÓN", result.feedback)
        self.assertNotIn("Esta recomendacion debe ser eliminada", result.feedback)

    def test_formats_titles_with_colon_joined_by_space(self):
        block = """**1. Argumentación**
**Fortalezas**
- Argumento uno ampliamente respaldado.
**Debilidades**
- Argumento dos requiere mas sustento documental.
"""

        result = self._extractor.extract(block)

        self.assertIn("Fortalezas:", result.feedback)
        self.assertIn("Debilidades:", result.feedback)
        kinds = [block.kind for block in result.blocks]
        self.assertIn(FeedbackBlockKind.TITLE, kinds)
        self.assertIn(FeedbackBlockKind.ITEM, kinds)

    def test_returns_unscored_dto_when_structure_parser_returns_empty_blocks(self):
        block = "## **1. Claridad** [Puntuación: 8/10]\n"

        result = self._extractor.extract(block)

        self.assertEqual(result.feedback, "No disponible")
        self.assertEqual(result.blocks, ())

    def test_returns_unscored_dto_when_formatted_feedback_is_shorter_than_ten_characters(self):
        block = """## **1. Claridad** [Puntuación: 8/10]
Corto.
"""

        result = self._extractor.extract(block)

        self.assertEqual(result.feedback, "No disponible")
        self.assertEqual(result.blocks, ())

    def test_returns_feedback_dto_when_formatted_feedback_is_at_least_ten_characters(self):
        block = """## **1. Claridad** [Puntuación: 8/10]
Diez caract
"""

        result = self._extractor.extract(block)

        self.assertEqual(result.feedback, "Diez caract")
        self.assertEqual(len(result.blocks), 1)

    def test_uses_custom_unscored_dimension_feedback(self):
        custom_unscored = DimensionScoreDTO(
            score=5.0,
            feedback="Sin informacion",
            feedback_blocks=(),
        )
        extractor = DimensionFeedbackExtractor(
            feedback_structure_parser=self._structure_parser,
            unscored_dimension=custom_unscored,
        )
        block = "## **1. Claridad**\n"

        result = extractor.extract(block)

        self.assertEqual(result.feedback, "Sin informacion")
        self.assertEqual(result.blocks, ())
