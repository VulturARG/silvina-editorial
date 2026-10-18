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
from src.domain.dtos.body_table_dto import BodyTableDTO
from src.domain.dtos.document_content_dto import DocumentContentDTO
from src.domain.enums.article_size import ArticleSize
from src.domain.tests.classification.fake_llm_generator_adapter import FakeLlmGeneratorAdapter

BODY_TITLE = "Título exclusivo del cuerpo"
PROMPT_TEMPLATE = "TITULO: {title}\nTEXTO: {text_sample}"
NEUTRAL_RESPONSE = "S4: NO\nS5: NO\nS6: NO"
TABLE_MARKDOWN = "| Name | Score |\n| --- | --- |\n| Ana | 9 |"


class TestArticleClassifierTables(TestCase):
    def test_prompt_contains_table_markdown_between_its_surrounding_paragraphs(self) -> None:
        document_content = self._build_document_content(
            body_paragraphs=("Antes de la tabla.", "Después de la tabla."),
            tables=(BodyTableDTO(markdown=TABLE_MARKDOWN, position=1),),
        )
        fake_llm_generator = FakeLlmGeneratorAdapter(responses=[NEUTRAL_RESPONSE])

        self._build_classifier(fake_llm_generator).classify(document_content)

        self.assertIn(
            f"TEXTO: Antes de la tabla.\n\n{TABLE_MARKDOWN}\n\nDespués de la tabla.",
            fake_llm_generator.received_prompts[0],
        )

    def test_text_sample_of_the_prompt_never_contains_the_body_title(self) -> None:
        document_content = self._build_document_content(
            body_paragraphs=("Primer párrafo.", "Segundo párrafo."),
            tables=(BodyTableDTO(markdown=TABLE_MARKDOWN, position=1),),
        )
        fake_llm_generator = FakeLlmGeneratorAdapter(responses=[NEUTRAL_RESPONSE])

        self._build_classifier(fake_llm_generator).classify(document_content)

        prompt = fake_llm_generator.received_prompts[0]
        text_sample = prompt.split("TEXTO: ", 1)[1]
        self.assertNotIn(BODY_TITLE, text_sample)
        self.assertIn(f"TITULO: {BODY_TITLE}\n", prompt)

    def test_huge_table_does_not_change_the_article_size_class(self) -> None:
        huge_table_markdown = "| Dato |\n| --- |\n" + "| " + "z" * 80_000 + " |"
        body_paragraphs = ("x" * 20_000,)
        document_without_table = self._build_document_content(
            body_paragraphs=body_paragraphs, tables=()
        )
        document_with_huge_table = self._build_document_content(
            body_paragraphs=body_paragraphs,
            tables=(BodyTableDTO(markdown=huge_table_markdown, position=1),),
        )

        result_without_table = self._build_classifier(
            FakeLlmGeneratorAdapter(responses=[NEUTRAL_RESPONSE])
        ).classify(document_without_table)
        result_with_huge_table = self._build_classifier(
            FakeLlmGeneratorAdapter(responses=[NEUTRAL_RESPONSE])
        ).classify(document_with_huge_table)

        self.assertEqual(result_without_table.article_size, ArticleSize.SHORT)
        self.assertEqual(result_with_huge_table.article_size, ArticleSize.SHORT)

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
            max_output_tokens=300,
            methodological_vocabulary_detector=MethodologicalVocabularyDetector(),
            reference_signal_detector=ReferenceSignalDetector(),
            rule_table=ClassificationRuleTable(),
        )

    def _build_document_content(
        self,
        body_paragraphs: tuple[str, ...],
        tables: tuple[BodyTableDTO, ...],
    ) -> DocumentContentDTO:
        body = ArticleBodyDTO(
            title=BODY_TITLE,
            abstract_paragraphs=(),
            paragraphs=body_paragraphs,
            tables=tables,
        )
        return DocumentContentDTO(
            word_count=100,
            char_count=body.char_count,
            paragraphs=list(body_paragraphs),
            title=BODY_TITLE,
            body=body,
        )
