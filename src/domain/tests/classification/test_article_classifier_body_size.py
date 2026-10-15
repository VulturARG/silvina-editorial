from unittest import TestCase

from src.domain.classification.article_classification_response_parser import (
    ArticleClassificationResponseParser,
)
from src.domain.classification.article_classifier import ArticleClassifier
from src.domain.classification.article_size_classifier import ArticleSizeClassifier
from src.domain.classification.classification_rule_table import ClassificationRuleTable
from src.domain.classification.imryd_signal_detector import ImrydSignalDetector
from src.domain.classification.methodological_vocabulary_detector import (
    MethodologicalVocabularyDetector,
)
from src.domain.classification.reference_signal_detector import ReferenceSignalDetector
from src.domain.dtos.article_body_dto import ArticleBodyDTO
from src.domain.dtos.article_size_thresholds_dto import ArticleSizeThresholdsDTO
from src.domain.dtos.document_content_dto import DocumentContentDTO
from src.domain.enums.article_size import ArticleSize
from src.domain.enums.article_type import ArticleType
from src.domain.enums.classification_confidence import ClassificationConfidence
from src.domain.exceptions.classification_errors import ClassificationFailed
from src.domain.tests.classification.fake_llm_generator_adapter import FakeLlmGeneratorAdapter

TITLE = "Título de prueba"
IMRYD_PARAGRAPHS = ["Introducción", "Metodología", "Resultados", "Discusión"]


class TestArticleClassifierBodySize(TestCase):
    def setUp(self) -> None:
        self._classifier = ArticleClassifier(
            llm_generator=FakeLlmGeneratorAdapter(responses=["S4: NO\nS5: NO\nS6: NO"]),
            signal_detector=ImrydSignalDetector(),
            article_size_classifier=ArticleSizeClassifier(
                thresholds=ArticleSizeThresholdsDTO(
                    short_min_chars=16000,
                    short_max_chars=24000,
                    undefined_min_chars=24001,
                    undefined_max_chars=35999,
                    long_min_chars=36000,
                    long_max_chars=40000,
                    extra_long_max_chars=75000,
                )
            ),
            response_parser=ArticleClassificationResponseParser(),
            signal_prompt_template="TITULO: {title}\nTEXTO: {text_sample}",
            temperature=0.1,
            num_predict=300,
            methodological_vocabulary_detector=MethodologicalVocabularyDetector(),
            reference_signal_detector=ReferenceSignalDetector(),
            rule_table=ClassificationRuleTable(),
        )

    def test_article_size_is_measured_over_body_not_document_char_count(self) -> None:
        document_content = self._build_document_content(
            document_char_count=1000, body_char_count=20000
        )

        result = self._classifier.classify(document_content)

        self.assertEqual(result.article_size, ArticleSize.SHORT)
        self.assertEqual(result.confidence, ClassificationConfidence.IMRYD_OVERRIDE)
        self.assertEqual(result.article_type, ArticleType.SCIENTIFIC)

    def test_extra_long_body_with_complete_imryd_structure_overrides_as_extra_long(self) -> None:
        document_content = self._build_document_content(
            document_char_count=1000, body_char_count=50000
        )

        result = self._classifier.classify(document_content)

        self.assertEqual(result.article_size, ArticleSize.EXTRA_LONG)
        self.assertEqual(result.confidence, ClassificationConfidence.IMRYD_OVERRIDE)

    def test_document_without_body_raises_classification_failed(self) -> None:
        document_content = DocumentContentDTO(
            word_count=100,
            char_count=20000,
            paragraphs=IMRYD_PARAGRAPHS,
            title=TITLE,
            body=None,
        )

        with self.assertRaises(ClassificationFailed):
            self._classifier.classify(document_content)

    def _build_document_content(
        self, document_char_count: int, body_char_count: int
    ) -> DocumentContentDTO:
        body_paragraph = "x" * (body_char_count - len(TITLE) - 1)
        return DocumentContentDTO(
            word_count=100,
            char_count=document_char_count,
            paragraphs=IMRYD_PARAGRAPHS,
            title=TITLE,
            body=ArticleBodyDTO(
                title=TITLE,
                abstract_paragraphs=(),
                paragraphs=(body_paragraph,),
            ),
        )
