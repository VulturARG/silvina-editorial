from json import loads
from os.path import join
from typing import Any

from dotenv import load_dotenv
from laya import load
from laya.agent import Agent

from src.application.analyze_document_use_case import AnalyzeDocumentUseCase
from src.domain.citation.apa_validator import ApaValidator
from src.domain.citation.citation_extractor import CitationExtractor
from src.domain.citation.citation_matcher import CitationMatcher
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
from src.domain.grammar.grammar_check_port import GrammarCheckPort
from src.domain.grammar.grammar_checker import GrammarChecker
from src.domain.laya.laya_decision_maker import LayaDecisionMaker
from src.domain.laya.laya_decision_port import LayaDecisionPort
from src.domain.laya.laya_text_sampler import LayaTextSampler
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
from src.infrastructure.adapters.laya.laya_decision_adapter import LayaDecisionAdapter
from src.infrastructure.adapters.llm_generator.ollama_generator_adapter import (
    OllamaGeneratorAdapter,
)
from src.infrastructure.env_config import EnvConfig
from src.infrastructure.resources.laya import LAYA_RESOURCES_DIR
from src.infrastructure.resources.prompts.quality import PROMPTS_DIR as QUALITY_PROMPTS_DIR
from src.infrastructure.resources.text_resource_loader import read_text_resource

load_dotenv()


class AnalyzeDocumentUseCaseWiring:
    """Composition root for the full document analysis pipeline."""

    def __init__(self) -> None:
        self._llm_generator_instance: LlmGeneratorPort | None = None
        self._env_config_instance: EnvConfig | None = None

    def create_use_case(self) -> AnalyzeDocumentUseCase:
        return AnalyzeDocumentUseCase(
            document_content_extractor=self._get_document_content_extractor(),
            citation_extractor=self._get_citation_extractor(),
            document_format_inspector=self._get_document_format_inspector(),
            grammar_checker=self._get_grammar_checker(),
            apa_validator=self._get_apa_validator(),
            laya_decision_maker=self._get_laya_decision_maker(),
            article_classifier=self._get_article_classifier(),
            quality_analyzer=self._get_quality_analyzer(),
            structure_validator=self._get_structure_validator(),
            citation_matcher=self._get_citation_matcher(),
            recommendation_builder=self._get_recommendation_builder(),
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

    def _get_laya_decision_maker(self) -> LayaDecisionMaker:
        return LayaDecisionMaker(
            text_sampler=self._get_laya_text_sampler(),
            laya_decision_port=self._get_laya_decision_port(),
        )

    def _get_laya_text_sampler(self) -> LayaTextSampler:
        return LayaTextSampler(
            text_sample_settings=self._get_env_config().get_laya_text_sample_settings()
        )

    def _get_laya_decision_port(self) -> LayaDecisionPort:
        return LayaDecisionAdapter(
            agent=self._get_laya_agent(), questions=self._get_laya_decision_questions()
        )

    def _get_laya_agent(self) -> Agent:
        env_config = self._get_env_config()
        return load(env_config.laya_checkpoint_path, device=env_config.laya_device)

    def _get_laya_decision_questions(self) -> dict[str, dict[str, Any]]:
        return loads(
            read_text_resource(directory=LAYA_RESOURCES_DIR, filename="decision_questions.json")
        )

    def _get_article_classifier(self) -> ArticleClassifier:
        return ArticleClassifier(
            signal_detector=ImrydSignalDetector(),
            article_size_classifier=self._get_article_size_classifier(),
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
            llm_generator=self._get_llm_generator(),
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
            llm_generator=self._get_llm_generator(),
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

    def _get_llm_generator(self) -> LlmGeneratorPort:
        if self._llm_generator_instance is None:
            env_config = self._get_env_config()
            self._llm_generator_instance = OllamaGeneratorAdapter(
                model_name=env_config.ollama_model_name, base_url=env_config.ollama_base_url
            )
        return self._llm_generator_instance
