from src.domain.classification.article_classification_response_parser import (
    ArticleClassificationResponseParser,
)
from src.domain.classification.article_classification_text_sampler import (
    ArticleClassificationTextSampler,
)
from src.domain.classification.article_size_classifier import ArticleSizeClassifier
from src.domain.classification.classification_rule_table import ClassificationRuleTable
from src.domain.classification.imryd_signal_detector import ImrydSignalDetector
from src.domain.classification.methodological_vocabulary_detector import (
    MethodologicalVocabularyDetector,
)
from src.domain.classification.reference_signal_detector import ReferenceSignalDetector
from src.domain.dtos.classification_result_dto import ClassificationResultDTO
from src.domain.dtos.classification_signals_dto import ClassificationSignalsDTO
from src.domain.dtos.document_content_dto import DocumentContentDTO
from src.domain.enums.article_size import ArticleSize
from src.domain.enums.article_type import ArticleType
from src.domain.enums.classification_confidence import ClassificationConfidence
from src.domain.exceptions.classification_errors import ClassificationFailed
from src.domain.ports.llm_generator_port import LlmGeneratorPort


class ArticleClassifier:
    """Domain service that classifies an academic article via a hybrid signal approach."""

    def __init__(
        self,
        llm_generator: LlmGeneratorPort,
        signal_detector: ImrydSignalDetector,
        article_size_classifier: ArticleSizeClassifier,
        text_sampler: ArticleClassificationTextSampler,
        response_parser: ArticleClassificationResponseParser,
        signal_prompt_template: str,
        temperature: float,
        num_predict: int,
        methodological_vocabulary_detector: MethodologicalVocabularyDetector,
        reference_signal_detector: ReferenceSignalDetector,
        rule_table: ClassificationRuleTable,
    ) -> None:
        self._llm_generator = llm_generator
        self._signal_detector = signal_detector
        self._article_size_classifier = article_size_classifier
        self._text_sampler = text_sampler
        self._response_parser = response_parser
        self._signal_prompt_template = signal_prompt_template
        self._temperature = temperature
        self._num_predict = num_predict
        self._methodological_vocabulary_detector = methodological_vocabulary_detector
        self._reference_signal_detector = reference_signal_detector
        self._rule_table = rule_table

    def classify(self, document_content: DocumentContentDTO) -> ClassificationResultDTO:
        """Classify a document into an ArticleType with confidence and reasoning."""
        if not document_content.paragraphs:
            raise ClassificationFailed()

        article_size = self._article_size_classifier.classify(
            char_count=document_content.char_count
        )

        imryd_signals = self._signal_detector.detect(document_content=document_content)
        if imryd_signals["imryd_complete"] and article_size != ArticleSize.OUT_OF_RANGE:
            return ClassificationResultDTO.create(
                article_type=ArticleType.SCIENTIFIC,
                article_size=article_size,
                confidence=ClassificationConfidence.IMRYD_OVERRIDE,
                reasoning="Estructura IMRyD completa detectada (override determinístico).",
            )

        text_sample = self._text_sampler.build_sample(document_content=document_content)
        has_research_intent, has_evidence_based_contribution, has_theoretical_justification = (
            self._detect_research_intent_signals(
                text_sample=text_sample, title=document_content.title
            )
        )
        signals = ClassificationSignalsDTO(
            has_sufficient_reference_count=self._reference_signal_detector.has_sufficient_count(
                document_content=document_content
            ),
            has_recent_references=self._reference_signal_detector.has_recent_majority(
                document_content=document_content
            ),
            has_methodological_vocabulary=self._methodological_vocabulary_detector.detect(
                document_content=document_content
            ),
            has_research_intent=has_research_intent,
            has_evidence_based_contribution=has_evidence_based_contribution,
            has_theoretical_justification=has_theoretical_justification,
        )

        return self._apply_rule(signals=signals, article_size=article_size)

    def _apply_rule(
        self, signals: ClassificationSignalsDTO, article_size: ArticleSize
    ) -> ClassificationResultDTO:
        signal_summary = self._describe_signals(signals=signals)
        matched_rule = self._rule_table.evaluate(signals=signals)
        return ClassificationResultDTO.create(
            article_type=matched_rule.article_type,
            article_size=article_size,
            confidence=matched_rule.confidence,
            reasoning=matched_rule.reasoning_template + signal_summary,
        )

    def _describe_signals(self, signals: ClassificationSignalsDTO) -> str:
        signal_labels = {
            "Referencias ≥ 12": signals.has_sufficient_reference_count,
            "Referencias recientes": signals.has_recent_references,
            "Vocabulario metodológico": signals.has_methodological_vocabulary,
            "Intención investigativa": signals.has_research_intent,
            "Contribución conclusiva": signals.has_evidence_based_contribution,
            "Justificación teórica": signals.has_theoretical_justification,
        }
        active = [label for label, value in signal_labels.items() if value]
        inactive = [label for label, value in signal_labels.items() if not value]

        parts = []
        if active:
            parts.append(f"Señales presentes: {', '.join(active)}.")
        if inactive:
            parts.append(f"Señales ausentes: {', '.join(inactive)}.")
        return " ".join(parts)

    def _detect_research_intent_signals(
        self, text_sample: str, title: str | None
    ) -> tuple[bool, bool, bool]:
        prompt = self._signal_prompt_template.format(title=title, text_sample=text_sample)
        response = self._llm_generator.generate(
            prompt=prompt,
            options={"temperature": self._temperature, "num_predict": self._num_predict},
        )
        return self._response_parser.parse(response_text=response)
