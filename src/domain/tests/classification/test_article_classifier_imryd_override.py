from unittest import TestCase

from src.domain.classification.article_classification_response_parser import (
    ArticleClassificationResponseParser,
)
from src.domain.classification.article_classification_text_sampler import (
    ArticleClassificationTextSampler,
)
from src.domain.classification.article_classifier import ArticleClassifier
from src.domain.classification.article_size_classifier import ArticleSizeClassifier
from src.domain.classification.classification_rule_table import ClassificationRuleTable
from src.domain.classification.imryd_signal_detector import ImrydSignalDetector
from src.domain.classification.methodological_vocabulary_detector import (
    MethodologicalVocabularyDetector,
)
from src.domain.classification.reference_signal_detector import ReferenceSignalDetector
from src.domain.dtos.article_size_thresholds_dto import ArticleSizeThresholdsDTO
from src.domain.dtos.document_content_dto import DocumentContentDTO
from src.domain.enums.article_type import ArticleType
from src.domain.enums.classification_confidence import ClassificationConfidence
from src.domain.exceptions.classification_errors import ClassificationFailed
from src.domain.tests.classification.fake_llm_generator_adapter import FakeLlmGeneratorAdapter


class TestArticleClassifierImrydOverride(TestCase):
    def setUp(self) -> None:
        self._fake_llm_generator = FakeLlmGeneratorAdapter(responses=["S4: NO\nS5: NO\nS6: NO"])

    def test_imryd_override_short_circuits_remaining_five_signals(self) -> None:
        classifier = self._build_classifier()
        document_content = self._build_document_content(imryd_paragraphs=True, char_count=20000)

        result = classifier.classify(document_content)

        self.assertEqual(result.article_type, ArticleType.SCIENTIFIC)
        self.assertEqual(result.confidence, ClassificationConfidence.IMRYD_OVERRIDE)
        self.assertEqual(self._fake_llm_generator.call_count, 0)

    def test_imryd_complete_but_article_size_out_of_range_does_not_override(self) -> None:
        classifier = self._build_classifier()
        document_content = self._build_document_content(imryd_paragraphs=True, char_count=1000)

        result = classifier.classify(document_content)

        self.assertNotEqual(result.confidence, ClassificationConfidence.IMRYD_OVERRIDE)
        self.assertEqual(self._fake_llm_generator.call_count, 1)

    def test_llm_call_passes_temperature_and_num_predict_as_options(self) -> None:
        classifier = self._build_classifier(temperature=0.1, num_predict=300)
        document_content = self._build_document_content(imryd_paragraphs=False, char_count=1000)

        classifier.classify(document_content)

        self.assertEqual(
            self._fake_llm_generator.received_options[0],
            {"temperature": 0.1, "num_predict": 300},
        )

    def test_constructor_without_temperature_or_num_predict_raises_type_error(self) -> None:
        with self.assertRaises(TypeError):
            ArticleClassifier(
                llm_generator=self._fake_llm_generator,
                signal_detector=ImrydSignalDetector(),
                article_size_classifier=ArticleSizeClassifier(
                    thresholds=ArticleSizeThresholdsDTO(
                        short_min_chars=16000,
                        short_max_chars=24000,
                        undefined_min_chars=24001,
                        undefined_max_chars=35999,
                        long_min_chars=36000,
                        long_max_chars=40000,
                    )
                ),
                text_sampler=ArticleClassificationTextSampler(),
                response_parser=ArticleClassificationResponseParser(),
                signal_prompt_template="TEXTO: {text_sample}",
                methodological_vocabulary_detector=MethodologicalVocabularyDetector(),
                reference_signal_detector=ReferenceSignalDetector(),
                rule_table=ClassificationRuleTable(),
            )

    def test_domain_service_has_zero_infrastructure_imports(self) -> None:
        import inspect

        from src.domain.classification import article_classifier

        source = inspect.getsource(article_classifier)

        self.assertNotIn("src.infrastructure", source)
        self.assertNotIn("import ollama", source)

    def test_empty_paragraphs_raises_classification_failed(self) -> None:
        classifier = self._build_classifier()
        document_content = DocumentContentDTO(word_count=0, char_count=0, paragraphs=[])

        with self.assertRaises(ClassificationFailed):
            classifier.classify(document_content)

    def _build_classifier(
        self, temperature: float = 0.1, num_predict: int = 300
    ) -> ArticleClassifier:
        return ArticleClassifier(
            llm_generator=self._fake_llm_generator,
            signal_detector=ImrydSignalDetector(),
            article_size_classifier=ArticleSizeClassifier(
                thresholds=ArticleSizeThresholdsDTO(
                    short_min_chars=16000,
                    short_max_chars=24000,
                    undefined_min_chars=24001,
                    undefined_max_chars=35999,
                    long_min_chars=36000,
                    long_max_chars=40000,
                )
            ),
            text_sampler=ArticleClassificationTextSampler(),
            response_parser=ArticleClassificationResponseParser(),
            signal_prompt_template="TITULO: {title}\nTEXTO: {text_sample}",
            temperature=temperature,
            num_predict=num_predict,
            methodological_vocabulary_detector=MethodologicalVocabularyDetector(),
            reference_signal_detector=ReferenceSignalDetector(),
            rule_table=ClassificationRuleTable(),
        )

    def _build_document_content(
        self, imryd_paragraphs: bool, char_count: int
    ) -> DocumentContentDTO:
        paragraphs = (
            ["Introducción", "Metodología", "Resultados", "Discusión"]
            if imryd_paragraphs
            else ["Texto de cuerpo sin encabezados de sección reconocibles."]
        )
        return DocumentContentDTO(
            word_count=100,
            char_count=char_count,
            paragraphs=paragraphs,
            title="Título de prueba",
        )
