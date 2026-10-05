from pathlib import Path
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
from src.domain.document.document_content_extractor import DocumentContentExtractor
from src.domain.dtos.article_size_thresholds_dto import ArticleSizeThresholdsDTO
from src.domain.dtos.classification_text_sampling_settings_dto import (
    ClassificationTextSamplingSettingsDTO,
)
from src.domain.enums.article_type import ArticleType
from src.domain.tests.classification.fake_llm_generator_adapter import FakeLlmGeneratorAdapter
from src.domain.tests.document.fake_character_count_port import FakeCharacterCountPort
from src.infrastructure.adapters.document.docx_reference_adapter import DocxReferenceAdapter
from src.infrastructure.adapters.document.docx_text_adapter import DocxTextAdapter
from src.infrastructure.adapters.document.paragraph_content_adapter import ParagraphContentAdapter
from src.infrastructure.resources.prompts.classification import PROMPTS_DIR
from src.infrastructure.resources.text_resource_loader import read_text_resource


class TestDocumentContentExtractorReferences(TestCase):
    """Regression test for DocumentContentExtractor reference population and signals S2a and S2b."""

    def test_extract_content_populates_references_and_triggers_scientific_signals(self) -> None:
        fixture_path = (
            Path(__file__).resolve().parents[3]
            / "tests"
            / "fixtures"
            / "capacidades_razonamiento_emergente_LLMs.docx"
        )
        docx_text_adapter = DocxTextAdapter()
        paragraph_content_adapter = ParagraphContentAdapter()
        docx_reference_adapter = DocxReferenceAdapter(document_text_port=docx_text_adapter)
        fake_character_count_port = FakeCharacterCountPort(result=None)

        document_content_extractor = DocumentContentExtractor(
            document_text_port=docx_text_adapter,
            content_extraction_port=paragraph_content_adapter,
            character_count_port=fake_character_count_port,
            reference_extraction_port=docx_reference_adapter,
        )
        document_content = document_content_extractor.extract_content(docx_path=str(fixture_path))

        self.assertGreaterEqual(len(document_content.references), 12)

        reference_signal_detector = ReferenceSignalDetector()
        self.assertTrue(reference_signal_detector.has_sufficient_count(document_content))
        self.assertTrue(reference_signal_detector.has_recent_majority(document_content))

        article_classifier = self._build_article_classifier()
        classification_result = article_classifier.classify(document_content=document_content)
        self.assertEqual(classification_result.article_type, ArticleType.SCIENTIFIC)

    def _build_article_classifier(self) -> ArticleClassifier:
        return ArticleClassifier(
            llm_generator=FakeLlmGeneratorAdapter(responses=["S4: SI\nS5: SI\nS6: SI"]),
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
            text_sampler=ArticleClassificationTextSampler(
                classification_text_sampling_settings=ClassificationTextSamplingSettingsDTO(
                    introduction_character_limit=3500,
                    conclusion_character_limit=2500,
                    fallback_character_limit=6000,
                    bibliography_header_max_length=30,
                )
            ),
            response_parser=ArticleClassificationResponseParser(),
            signal_prompt_template=read_text_resource(
                directory=PROMPTS_DIR, filename="s4_s5_s6_signal_prompt.txt"
            ),
            temperature=0.1,
            num_predict=300,
            methodological_vocabulary_detector=MethodologicalVocabularyDetector(),
            reference_signal_detector=ReferenceSignalDetector(),
            rule_table=ClassificationRuleTable(),
        )
