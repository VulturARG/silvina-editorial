from dataclasses import FrozenInstanceError
from unittest import TestCase

from src.domain.dtos.base_dto import BaseDTO
from src.domain.dtos.classification_result_dto import ClassificationResultDTO
from src.domain.enums.article_size import ArticleSize
from src.domain.enums.article_type import ArticleType


class TestClassificationResultDTO(TestCase):
    def test_classification_result_is_subclass_of_base_dto(self):
        self.assertTrue(issubclass(ClassificationResultDTO, BaseDTO))

    def test_classification_result_instantiation_with_correct_fields(self):
        result = ClassificationResultDTO(
            article_type=ArticleType.SCIENTIFIC,
            article_size=ArticleSize.LONG,
            confidence=0.9,
            reasoning="Well structured article",
        )
        self.assertEqual(result.article_type, ArticleType.SCIENTIFIC)
        self.assertEqual(result.article_size, ArticleSize.LONG)
        self.assertAlmostEqual(result.confidence, 0.9)
        self.assertEqual(result.reasoning, "Well structured article")

    def test_classification_result_is_immutable(self):
        result = ClassificationResultDTO(
            article_type=ArticleType.SCIENTIFIC,
            article_size=ArticleSize.LONG,
            confidence=0.8,
            reasoning="Test",
        )
        with self.assertRaises(FrozenInstanceError):
            result.confidence = 0.5

    def test_create_factory_builds_valid_instance(self):
        result = ClassificationResultDTO.create(
            article_type=ArticleType.OPINION,
            article_size=ArticleSize.SHORT,
            confidence=0.75,
            reasoning="Opinion piece",
        )
        self.assertEqual(result.article_type, ArticleType.OPINION)
        self.assertEqual(result.article_size, ArticleSize.SHORT)
        self.assertIsNotNone(result.timestamp)

    def test_create_factory_with_none_confidence(self):
        result = ClassificationResultDTO.create(
            article_type=ArticleType.UNKNOWN,
            article_size=ArticleSize.OUT_OF_RANGE,
            confidence=None,
            reasoning="Unknown",
        )
        self.assertIsNone(result.confidence)

    def test_create_factory_result_is_frozen(self):
        result = ClassificationResultDTO.create(
            article_type=ArticleType.SCIENTIFIC,
            article_size=ArticleSize.LONG,
            confidence=0.9,
            reasoning="Test",
        )
        with self.assertRaises(FrozenInstanceError):
            result.reasoning = "Modified"

    def test_effective_structure_type_scientific_with_imryd(self):
        result = ClassificationResultDTO(
            article_type=ArticleType.SCIENTIFIC,
            article_size=ArticleSize.LONG,
            confidence=0.9,
            reasoning="El documento sigue la estructura IMRyD.",
        )
        self.assertEqual(result.effective_structure_type, ArticleType.SCIENTIFIC)

    def test_effective_structure_type_scientific_without_imryd(self):
        result = ClassificationResultDTO(
            article_type=ArticleType.SCIENTIFIC,
            article_size=ArticleSize.LONG,
            confidence=0.9,
            reasoning="Ensayo de opinión libre",
        )
        self.assertEqual(result.effective_structure_type, ArticleType.POPULAR_SCIENCE)

    def test_effective_structure_type_non_scientific_returned_as_is(self):
        result = ClassificationResultDTO(
            article_type=ArticleType.POPULAR_SCIENCE,
            article_size=ArticleSize.LONG,
            confidence=0.8,
            reasoning="",
        )
        self.assertEqual(result.effective_structure_type, ArticleType.POPULAR_SCIENCE)

    def test_effective_structure_type_opinion_returned_as_is(self):
        result = ClassificationResultDTO(
            article_type=ArticleType.OPINION,
            article_size=ArticleSize.SHORT,
            confidence=0.7,
            reasoning="",
        )
        self.assertEqual(result.effective_structure_type, ArticleType.OPINION)

    def test_effective_structure_type_scientific_none_reasoning(self):
        result = ClassificationResultDTO(
            article_type=ArticleType.SCIENTIFIC,
            article_size=ArticleSize.LONG,
            confidence=0.9,
            reasoning=None,
        )
        self.assertEqual(result.effective_structure_type, ArticleType.POPULAR_SCIENCE)

    def test_str_contains_enum_values_and_confidence_percentage(self):
        result = ClassificationResultDTO(
            article_type=ArticleType.SCIENTIFIC,
            article_size=ArticleSize.LONG,
            confidence=0.9,
            reasoning="Test",
        )
        string_repr = str(result)
        self.assertIn("científico", string_repr)
        self.assertIn("largo", string_repr)
        self.assertIn("%", string_repr)
