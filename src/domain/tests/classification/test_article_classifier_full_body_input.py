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
from src.domain.tests.classification.fake_llm_generator_adapter import FakeLlmGeneratorAdapter

BODY_TITLE = "Título del cuerpo del artículo"
HEADER_TITLE = "Encabezado del documento Word"
PROMPT_TEMPLATE = "TITULO: {title}\nTEXTO: {text_sample}"
NEUTRAL_RESPONSE = "S4: NO\nS5: NO\nS6: NO"


class TestArticleClassifierFullBodyInput(TestCase):
    def test_prompt_contains_body_title_and_every_body_paragraph_in_order(self) -> None:
        body_paragraphs = ("Primer párrafo del cuerpo.", "Segundo párrafo.", "Tercer párrafo.")
        document_content = self._build_document_content(
            body_title=BODY_TITLE, body_paragraphs=body_paragraphs
        )
        fake_llm_generator = FakeLlmGeneratorAdapter(responses=[NEUTRAL_RESPONSE])

        self._build_classifier(fake_llm_generator).classify(document_content)

        prompt = fake_llm_generator.received_prompts[0]
        self.assertIn(f"TITULO: {BODY_TITLE}\n", prompt)
        self.assertIn(f"TEXTO: {' '.join(body_paragraphs)}", prompt)

    def test_body_much_longer_than_former_limits_reaches_prompt_uncut(self) -> None:
        first_paragraph = "INICIO " + "a" * 99_990
        last_paragraph = "b" * 99_990 + " FINAL"
        body_paragraphs = (first_paragraph, last_paragraph)
        document_content = self._build_document_content(
            body_title=BODY_TITLE, body_paragraphs=body_paragraphs
        )
        fake_llm_generator = FakeLlmGeneratorAdapter(responses=[NEUTRAL_RESPONSE])

        self._build_classifier(fake_llm_generator).classify(document_content)

        prompt = fake_llm_generator.received_prompts[0]
        self.assertIn(" ".join(body_paragraphs), prompt)
        self.assertIn("INICIO", prompt)
        self.assertIn("FINAL", prompt)

    def test_document_header_title_is_not_sent_to_prompt_when_body_title_differs(self) -> None:
        document_content = self._build_document_content(
            body_title=BODY_TITLE,
            body_paragraphs=("Texto de cuerpo sin encabezados reconocibles.",),
            header_title=HEADER_TITLE,
        )
        fake_llm_generator = FakeLlmGeneratorAdapter(responses=[NEUTRAL_RESPONSE])

        self._build_classifier(fake_llm_generator).classify(document_content)

        prompt = fake_llm_generator.received_prompts[0]
        self.assertIn(BODY_TITLE, prompt)
        self.assertNotIn(HEADER_TITLE, prompt)

    def _build_classifier(self, fake_llm_generator: FakeLlmGeneratorAdapter) -> ArticleClassifier:
        return ArticleClassifier(
            llm_generator=fake_llm_generator,
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
            signal_prompt_template=PROMPT_TEMPLATE,
            temperature=0.1,
            num_predict=300,
            methodological_vocabulary_detector=MethodologicalVocabularyDetector(),
            reference_signal_detector=ReferenceSignalDetector(),
            rule_table=ClassificationRuleTable(),
        )

    def _build_document_content(
        self,
        body_title: str,
        body_paragraphs: tuple[str, ...],
        header_title: str | None = None,
    ) -> DocumentContentDTO:
        body_char_count = len(" ".join((body_title, *body_paragraphs)))
        return DocumentContentDTO(
            word_count=100,
            char_count=body_char_count,
            paragraphs=list(body_paragraphs),
            title=header_title if header_title is not None else body_title,
            body=ArticleBodyDTO(
                title=body_title,
                abstract_paragraphs=(),
                paragraphs=body_paragraphs,
            ),
        )
