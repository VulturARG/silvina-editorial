from inspect import getsource
from unittest import TestCase

from src.domain.classification import article_classifier
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
from src.domain.dtos.laya_choice_decision_dto import LayaChoiceDecisionDTO
from src.domain.dtos.laya_decision_result_dto import LayaDecisionResultDTO
from src.domain.enums.article_type import ArticleType
from src.domain.enums.classification_confidence import ClassificationConfidence
from src.domain.exceptions.classification_errors import ClassificationFailed
from src.domain.tests.laya.fake_laya_decision_port import DEFAULT_DECISION_RESULT


def build_laya_decision(
    research_intent: str, empirical_evidence: str, theoretical_framework: str
) -> LayaDecisionResultDTO:
    return LayaDecisionResultDTO.from_dict(
        {
            **DEFAULT_DECISION_RESULT.as_dict(),
            "s4_research_intent": build_choice(research_intent).as_dict(),
            "s5_empirical_evidence": build_choice(empirical_evidence).as_dict(),
            "s6_theoretical_framework": build_choice(theoretical_framework).as_dict(),
        }
    )


def build_choice(answer: str) -> LayaChoiceDecisionDTO:
    return LayaChoiceDecisionDTO(answer=answer, probabilities={answer: 1.0}, confidence=1.0)


def build_classifier() -> ArticleClassifier:
    return ArticleClassifier(
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
        methodological_vocabulary_detector=MethodologicalVocabularyDetector(),
        reference_signal_detector=ReferenceSignalDetector(),
        rule_table=ClassificationRuleTable(),
    )


def build_document_content(imryd_paragraphs: bool, char_count: int) -> DocumentContentDTO:
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


class TestArticleClassifier(TestCase):
    def test_imryd_override_classifies_as_scientific_regardless_of_laya_signals(self):
        result = build_classifier().classify(
            document_content=build_document_content(imryd_paragraphs=True, char_count=20000),
            laya_decision=build_laya_decision("NO", "NO", "NO"),
        )

        self.assertEqual(result.article_type, ArticleType.SCIENTIFIC)
        self.assertEqual(result.confidence, ClassificationConfidence.IMRYD_OVERRIDE)

    def test_imryd_complete_but_article_size_out_of_range_does_not_override(self):
        result = build_classifier().classify(
            document_content=build_document_content(imryd_paragraphs=True, char_count=1000),
            laya_decision=build_laya_decision("NO", "NO", "NO"),
        )

        self.assertNotEqual(result.confidence, ClassificationConfidence.IMRYD_OVERRIDE)

    def test_positive_laya_answers_become_present_signals(self):
        result = build_classifier().classify(
            document_content=build_document_content(imryd_paragraphs=False, char_count=20000),
            laya_decision=build_laya_decision("SI", "SI", "SI"),
        )

        present_signals = result.reasoning.split("Señales presentes:")[1].split(".")[0]
        self.assertIn("Intención investigativa", present_signals)
        self.assertIn("Contribución conclusiva", present_signals)
        self.assertIn("Justificación teórica", present_signals)

    def test_negative_laya_answers_become_absent_signals(self):
        result = build_classifier().classify(
            document_content=build_document_content(imryd_paragraphs=False, char_count=20000),
            laya_decision=build_laya_decision("NO", "NO", "NO"),
        )

        absent_signals = result.reasoning.split("Señales ausentes:")[1]
        self.assertIn("Intención investigativa", absent_signals)
        self.assertIn("Contribución conclusiva", absent_signals)
        self.assertIn("Justificación teórica", absent_signals)

    def test_each_laya_answer_maps_to_its_own_signal(self):
        result = build_classifier().classify(
            document_content=build_document_content(imryd_paragraphs=False, char_count=20000),
            laya_decision=build_laya_decision("SI", "NO", "SI"),
        )

        absent_signals = result.reasoning.split("Señales ausentes:")[1]
        self.assertIn("Contribución conclusiva", absent_signals)
        self.assertNotIn("Intención investigativa", absent_signals)
        self.assertNotIn("Justificación teórica", absent_signals)

    def test_empty_paragraphs_raises_classification_failed(self):
        with self.assertRaises(ClassificationFailed):
            build_classifier().classify(
                document_content=DocumentContentDTO(word_count=0, char_count=0, paragraphs=[]),
                laya_decision=build_laya_decision("SI", "SI", "SI"),
            )

    def test_domain_service_has_zero_infrastructure_imports(self):
        source = getsource(article_classifier)
        self.assertNotIn("src.infrastructure", source)
        self.assertNotIn("import ollama", source)
