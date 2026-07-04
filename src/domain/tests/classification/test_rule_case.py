from unittest import TestCase

from src.domain.classification.has_methodological_vocabulary_specification import (
    HasMethodologicalVocabularySpecification,
)
from src.domain.classification.rule_case import RuleCase
from src.domain.enums.article_type import ArticleType
from src.domain.enums.classification_confidence import ClassificationConfidence


class TestRuleCase(TestCase):
    def test_field_values_match_constructor_arguments(self) -> None:
        specification = HasMethodologicalVocabularySpecification()
        rule_case = RuleCase(
            specification=specification,
            article_type=ArticleType.SCIENTIFIC,
            confidence=ClassificationConfidence.FULL_SIGNAL_MATCH,
            reasoning_template="Texto de ejemplo. ",
        )

        self.assertIs(rule_case.specification, specification)
        self.assertEqual(rule_case.article_type, ArticleType.SCIENTIFIC)
        self.assertEqual(rule_case.confidence, ClassificationConfidence.FULL_SIGNAL_MATCH)
        self.assertEqual(rule_case.reasoning_template, "Texto de ejemplo. ")

    def test_confidence_accepts_none(self) -> None:
        rule_case = RuleCase(
            specification=HasMethodologicalVocabularySpecification(),
            article_type=ArticleType.POPULAR_SCIENCE,
            confidence=None,
            reasoning_template="Texto de ejemplo. ",
        )

        self.assertIsNone(rule_case.confidence)
