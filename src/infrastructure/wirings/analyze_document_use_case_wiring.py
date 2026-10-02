from os.path import join

from dotenv import load_dotenv

from src.application.analyze_document_use_case import AnalyzeDocumentUseCase
from src.domain.citation.apa_validator import ApaValidator
from src.domain.citation.citation_extractor import CitationExtractor
from src.domain.citation.citation_matcher import CitationMatcher
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
from src.domain.document.character_count_port import CharacterCountPort
from src.domain.document.citation_extraction_port import CitationExtractionPort
from src.domain.document.content_extraction_port import ContentExtractionPort
from src.domain.document.document_content_extractor import DocumentContentExtractor
from src.domain.document.document_format_inspection_port import DocumentFormatInspectionPort
from src.domain.document.document_format_inspector import DocumentFormatInspector
from src.domain.document.document_text_port import DocumentTextPort
from src.domain.document.reference_extraction_port import ReferenceExtractionPort
from src.domain.dtos.article_size_thresholds_dto import ArticleSizeThresholdsDTO
from src.domain.enums.ai_provider import AiProvider
from src.domain.enums.ai_purpose import AiPurpose
from src.domain.grammar.grammar_check_port import GrammarCheckPort
from src.domain.grammar.grammar_checker import GrammarChecker
from src.domain.metrics.analysis_context_port import AnalysisContextPort
from src.domain.metrics.analysis_metrics_port import AnalysisMetricsPort
from src.domain.metrics.analysis_metrics_recorder import AnalysisMetricsRecorder
from src.domain.metrics.analysis_tracker import AnalysisTracker
from src.domain.metrics.audit_payload_policy import AuditPayloadPolicy
from src.domain.ports.llm_generator_port import LlmGeneratorPort
from src.domain.quality.editorial_suitability_analyzer import EditorialSuitabilityAnalyzer
from src.domain.quality.editorial_suitability_parser import EditorialSuitabilityParser
from src.domain.quality.quality_analyzer import QualityAnalyzer
from src.domain.quality.quality_response_parser import QualityResponseParser
from src.domain.quality.quality_text_sampler import QualityTextSampler
from src.domain.recommendation.recommendation_builder import RecommendationBuilder
from src.domain.structure.structure_validator import StructureValidator
from src.infrastructure.adapters.document.docx_citation_adapter import DocxCitationAdapter
from src.infrastructure.adapters.document.docx_eumic_adapter import DocxEumicAdapter
from src.infrastructure.adapters.document.docx_reference_adapter import DocxReferenceAdapter
from src.infrastructure.adapters.document.docx_text_adapter import DocxTextAdapter
from src.infrastructure.adapters.document.paragraph_content_adapter import ParagraphContentAdapter
from src.infrastructure.adapters.document.win32com_word_count_adapter import (
    Win32ComWordCountAdapter,
)
from src.infrastructure.adapters.gateway.file_gateway_adapter import FileGatewayAdapter
from src.infrastructure.adapters.grammar.language_tool_adapter import LanguageToolAdapter
from src.infrastructure.adapters.llm_generator.audited_llm_generator_adapter import (
    AuditedLlmGeneratorAdapter,
)
from src.infrastructure.adapters.llm_generator.ollama_generator_adapter import (
    OllamaGeneratorAdapter,
)
from src.infrastructure.adapters.metrics.analysis_context_adapter import AnalysisContextAdapter
from src.infrastructure.adapters.metrics.fail_safe_analysis_metrics_adapter import (
    FailSafeAnalysisMetricsAdapter,
)
from src.infrastructure.adapters.metrics.sqlite_analysis_metrics_adapter import (
    SqliteAnalysisMetricsAdapter,
)
from src.infrastructure.env_config import EnvConfig
from src.infrastructure.resources.prompts.classification import (
    PROMPTS_DIR as CLASSIFICATION_PROMPTS_DIR,
)
from src.infrastructure.resources.prompts.quality import PROMPTS_DIR as QUALITY_PROMPTS_DIR
from src.infrastructure.resources.text_resource_loader import read_text_resource

load_dotenv()


class AnalyzeDocumentUseCaseWiring:
    """Composition root for the full document analysis pipeline."""

    def __init__(self) -> None:
        self._ollama_generator_instance: LlmGeneratorPort | None = None
        self._env_config_instance: EnvConfig | None = None
        self._analysis_metrics_port_instance: AnalysisMetricsPort | None = None
        self._audit_payload_policy_instance: AuditPayloadPolicy | None = None

    def create_use_case(self) -> AnalyzeDocumentUseCase:
        return AnalyzeDocumentUseCase(
            document_content_extractor=self._get_document_content_extractor(),
            citation_extractor=self._get_citation_extractor(),
            document_format_inspector=self._get_document_format_inspector(),
            grammar_checker=self._get_grammar_checker(),
            apa_validator=self._get_apa_validator(),
            article_classifier=self._get_article_classifier(),
            quality_analyzer=self._get_quality_analyzer(),
            structure_validator=self._get_structure_validator(),
            citation_matcher=self._get_citation_matcher(),
            recommendation_builder=self._get_recommendation_builder(),
            analysis_tracker=self._get_analysis_tracker(),
        )

    def _get_env_config(self) -> EnvConfig:
        if self._env_config_instance is None:
            self._env_config_instance = EnvConfig()
        return self._env_config_instance

    def _get_document_text_port(self) -> DocumentTextPort:
        return DocxTextAdapter()

    def _get_content_extraction_port(self) -> ContentExtractionPort:
        return ParagraphContentAdapter()

    def _get_character_count_port(self) -> CharacterCountPort:
        return Win32ComWordCountAdapter()

    def _get_citation_extraction_port(self) -> CitationExtractionPort:
        env_config = self._get_env_config()
        return DocxCitationAdapter(
            document_text_port=self._get_document_text_port(),
            max_author_name_length=env_config.citation_max_author_name_length,
        )

    def _get_reference_extraction_port(self) -> ReferenceExtractionPort:
        return DocxReferenceAdapter(document_text_port=self._get_document_text_port())

    def _get_grammar_check_port(self) -> GrammarCheckPort:
        env_config = self._get_env_config()
        return LanguageToolAdapter(max_replacements=env_config.grammar_max_replacements)

    def _get_document_format_inspection_port(self) -> DocumentFormatInspectionPort:
        return DocxEumicAdapter()

    def _get_document_content_extractor(self) -> DocumentContentExtractor:
        return DocumentContentExtractor(
            document_text_port=self._get_document_text_port(),
            content_extraction_port=self._get_content_extraction_port(),
            character_count_port=self._get_character_count_port(),
            reference_extraction_port=self._get_reference_extraction_port(),
        )

    def _get_citation_extractor(self) -> CitationExtractor:
        return CitationExtractor(
            citation_extraction_port=self._get_citation_extraction_port(),
            reference_extraction_port=self._get_reference_extraction_port(),
        )

    def _get_document_format_inspector(self) -> DocumentFormatInspector:
        return DocumentFormatInspector(
            document_format_inspection_port=self._get_document_format_inspection_port()
        )

    def _get_grammar_checker(self) -> GrammarChecker:
        return GrammarChecker(grammar_check_port=self._get_grammar_check_port())

    def _get_apa_validator(self) -> ApaValidator:
        return ApaValidator()

    def _get_citation_matcher(self) -> CitationMatcher:
        return CitationMatcher()

    def _get_structure_validator(self) -> StructureValidator:
        env_config = self._get_env_config()
        return StructureValidator(max_header_length=env_config.structure_max_header_length)

    def _get_recommendation_builder(self) -> RecommendationBuilder:
        return RecommendationBuilder(settings=self._get_env_config().get_recommendation_settings())

    def _get_article_classifier(self) -> ArticleClassifier:
        env_config = self._get_env_config()
        return ArticleClassifier(
            llm_generator=self._get_llm_generator(purpose=AiPurpose.ARTICLE_CLASSIFICATION),
            signal_detector=ImrydSignalDetector(),
            article_size_classifier=self._get_article_size_classifier(),
            text_sampler=ArticleClassificationTextSampler(),
            response_parser=ArticleClassificationResponseParser(),
            signal_prompt_template=read_text_resource(
                directory=CLASSIFICATION_PROMPTS_DIR, filename="s4_s5_s6_signal_prompt.txt"
            ),
            temperature=env_config.article_classifier_temperature,
            num_predict=env_config.article_classifier_num_predict,
            methodological_vocabulary_detector=MethodologicalVocabularyDetector(),
            reference_signal_detector=ReferenceSignalDetector(),
            rule_table=ClassificationRuleTable(),
        )

    def _get_article_size_classifier(self) -> ArticleSizeClassifier:
        return ArticleSizeClassifier(thresholds=self._get_article_size_thresholds())

    def _get_article_size_thresholds(self) -> ArticleSizeThresholdsDTO:
        env_config = self._get_env_config()
        return ArticleSizeThresholdsDTO(
            short_min_chars=env_config.article_size_short_min_chars,
            short_max_chars=env_config.article_size_short_max_chars,
            undefined_min_chars=env_config.article_size_undefined_min_chars,
            undefined_max_chars=env_config.article_size_undefined_max_chars,
            long_min_chars=env_config.article_size_long_min_chars,
            long_max_chars=env_config.article_size_long_max_chars,
        )

    def _get_quality_analyzer(self) -> QualityAnalyzer:
        return QualityAnalyzer(
            llm_generator=self._get_llm_generator(purpose=AiPurpose.QUALITY_ANALYSIS),
            text_sampler=self._get_quality_text_sampler(),
            response_parser=QualityResponseParser(),
            clarity_coherence_prompt_template=read_text_resource(
                directory=QUALITY_PROMPTS_DIR, filename="clarity_coherence_prompt.txt"
            ),
            argumentation_conclusions_prompt_template=read_text_resource(
                directory=QUALITY_PROMPTS_DIR, filename="argumentation_conclusions_prompt.txt"
            ),
            editorial_suitability_analyzer=self._get_editorial_suitability_analyzer(),
        )

    def _get_editorial_suitability_analyzer(self) -> EditorialSuitabilityAnalyzer:
        return EditorialSuitabilityAnalyzer(
            llm_generator=self._get_llm_generator(purpose=AiPurpose.EDITORIAL_SUITABILITY),
            parser=EditorialSuitabilityParser(),
            contribution_prompt_template=read_text_resource(
                directory=QUALITY_PROMPTS_DIR, filename="contribution_prompt.txt"
            ),
            alignment_prompt_template=read_text_resource(
                directory=QUALITY_PROMPTS_DIR, filename="alignment_prompt.txt"
            ),
            research_lines=FileGatewayAdapter().read(
                join(QUALITY_PROMPTS_DIR, "research_lines.txt")
            ),
        )

    def _get_quality_text_sampler(self) -> QualityTextSampler:
        env_config = self._get_env_config()
        return QualityTextSampler(
            min_sample_word_count=env_config.quality_min_sample_word_count,
            text_sample_character_limit=env_config.quality_text_sample_character_limit,
        )

    def _get_ollama_generator(self) -> LlmGeneratorPort:
        if self._ollama_generator_instance is None:
            env_config = self._get_env_config()
            self._ollama_generator_instance = OllamaGeneratorAdapter(
                model_name=env_config.ollama_model_name,
                base_url=env_config.ollama_base_url,
                think=env_config.ollama_think,
            )
        return self._ollama_generator_instance

    def _get_analysis_context_port(self) -> AnalysisContextPort:
        return AnalysisContextAdapter()

    def _get_analysis_metrics_port(self) -> AnalysisMetricsPort:
        if self._analysis_metrics_port_instance is None:
            env_config = self._get_env_config()
            self._analysis_metrics_port_instance = FailSafeAnalysisMetricsAdapter(
                analysis_metrics_port=SqliteAnalysisMetricsAdapter(
                    database_path=env_config.metrics_database_path
                )
            )
        return self._analysis_metrics_port_instance

    def _get_audit_payload_policy(self) -> AuditPayloadPolicy:
        if self._audit_payload_policy_instance is None:
            env_config = self._get_env_config()
            self._audit_payload_policy_instance = AuditPayloadPolicy(app_mode=env_config.app_mode)
        return self._audit_payload_policy_instance

    def _get_llm_generator(self, purpose: AiPurpose) -> LlmGeneratorPort:
        env_config = self._get_env_config()
        return AuditedLlmGeneratorAdapter(
            generator=self._get_ollama_generator(),
            metrics_port=self._get_analysis_metrics_port(),
            analysis_context_port=self._get_analysis_context_port(),
            provider=AiProvider.OLLAMA,
            model_name=env_config.ollama_model_name,
            purpose=purpose,
            audit_payload_policy=self._get_audit_payload_policy(),
        )

    def _get_analysis_metrics_recorder(self) -> AnalysisMetricsRecorder:
        return AnalysisMetricsRecorder(metrics_port=self._get_analysis_metrics_port())

    def _get_analysis_tracker(self) -> AnalysisTracker:
        return AnalysisTracker(
            metrics_recorder=self._get_analysis_metrics_recorder(),
            analysis_context_port=self._get_analysis_context_port(),
        )
