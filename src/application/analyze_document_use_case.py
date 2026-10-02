from functools import partial

from src.domain.citation.apa_validator import ApaValidator
from src.domain.citation.citation_extractor import CitationExtractor
from src.domain.citation.citation_matcher import CitationMatcher
from src.domain.classification.article_classifier import ArticleClassifier
from src.domain.document.document_content_extractor import DocumentContentExtractor
from src.domain.document.document_format_inspector import DocumentFormatInspector
from src.domain.dtos.apa_validation_result_dto import ApaValidationResultDTO
from src.domain.dtos.citation_dto import CitationDTO
from src.domain.dtos.document_content_dto import DocumentContentDTO
from src.domain.dtos.report_input_dto import ReportInputDTO
from src.domain.dtos.structure_validation_result_dto import StructureValidationResultDTO
from src.domain.enums.analysis_stage import AnalysisStage
from src.domain.enums.article_type import ArticleType
from src.domain.enums.section_name import SectionName
from src.domain.exceptions.decorators.generic_error_handler import generic_error_handler
from src.domain.grammar.grammar_checker import GrammarChecker
from src.domain.metrics.analysis_tracker import AnalysisTracker
from src.domain.quality.quality_analyzer import QualityAnalyzer
from src.domain.recommendation.recommendation_builder import RecommendationBuilder
from src.domain.structure.structure_validator import StructureValidator


class AnalyzeDocumentUseCase:
    """Orchestrates the complete academic document analysis pipeline."""

    def __init__(
        self,
        document_content_extractor: DocumentContentExtractor,
        citation_extractor: CitationExtractor,
        document_format_inspector: DocumentFormatInspector,
        grammar_checker: GrammarChecker,
        apa_validator: ApaValidator,
        article_classifier: ArticleClassifier,
        quality_analyzer: QualityAnalyzer,
        structure_validator: StructureValidator,
        citation_matcher: CitationMatcher,
        recommendation_builder: RecommendationBuilder,
        analysis_tracker: AnalysisTracker,
    ) -> None:
        self._document_content_extractor = document_content_extractor
        self._citation_extractor = citation_extractor
        self._document_format_inspector = document_format_inspector
        self._grammar_checker = grammar_checker
        self._apa_validator = apa_validator
        self._article_classifier = article_classifier
        self._quality_analyzer = quality_analyzer
        self._structure_validator = structure_validator
        self._citation_matcher = citation_matcher
        self._recommendation_builder = recommendation_builder
        self._analysis_tracker = analysis_tracker

    @generic_error_handler
    def execute(self, document_path: str) -> ReportInputDTO:
        """Run the complete document analysis pipeline and return aggregated results."""
        return self._analysis_tracker.track_analysis(
            document_name=document_path,
            pipeline=partial(self._run_pipeline, document_path),
        )

    def _run_pipeline(self, document_path: str) -> ReportInputDTO:
        document_content = self._analysis_tracker.track_stage(
            AnalysisStage.EXTRACT_CONTENT,
            self._document_content_extractor.extract_content,
            docx_path=document_path,
        )
        citations, references, section_type = self._analysis_tracker.track_stage(
            AnalysisStage.EXTRACT_CITATIONS,
            self._citation_extractor.extract_citations_and_references,
            docx_path=document_path,
        )
        apa_validation = self._analysis_tracker.track_stage(
            AnalysisStage.VALIDATE_APA,
            self._validate_apa,
            citations=citations,
            paragraphs=document_content.paragraphs,
        )
        grammar = self._analysis_tracker.track_stage(
            AnalysisStage.CHECK_GRAMMAR,
            self._grammar_checker.check_grammar,
            paragraphs=document_content.paragraphs,
        )
        classification = self._analysis_tracker.track_stage(
            AnalysisStage.CLASSIFY_ARTICLE,
            self._article_classifier.classify,
            document_content=document_content,
        )
        quality = self._analysis_tracker.track_stage(
            AnalysisStage.ANALYZE_QUALITY,
            self._quality_analyzer.analyze,
            document_content=document_content,
        )

        effective_type = classification.effective_structure_type
        has_references = len(references) > 0
        structure = self._analysis_tracker.track_stage(
            AnalysisStage.VALIDATE_STRUCTURE,
            self._validate_structure,
            document_content=document_content,
            article_type=effective_type,
            has_references=has_references,
        )

        try:
            section_name = SectionName(section_type)
        except ValueError:
            section_name = SectionName.REFERENCES

        matched_citations = self._analysis_tracker.track_stage(
            AnalysisStage.MATCH_CITATIONS,
            self._citation_matcher.match_citations_to_references,
            citations=citations,
            references=references,
            section_type=section_name,
        )
        eumic_violations = self._analysis_tracker.track_stage(
            AnalysisStage.INSPECT_FORMAT,
            self._document_format_inspector.inspect,
            docx_path=document_path,
            word_count=document_content.word_count,
        )
        recommendations, verdict = self._analysis_tracker.track_stage(
            AnalysisStage.BUILD_RECOMMENDATIONS,
            self._recommendation_builder.build,
            classification=classification,
            quality=quality,
            structure=structure,
            citations=matched_citations,
            apa_validation=apa_validation,
            grammar=grammar,
        )

        return ReportInputDTO(
            filename=document_path,
            document_content=document_content,
            classification=classification,
            quality=quality,
            grammar=grammar,
            structure=structure,
            citations=matched_citations,
            apa_validation=apa_validation,
            recommendations=recommendations,
            verdict=verdict,
            eumic_violations=eumic_violations,
        )

    def _validate_apa(
        self, citations: list[CitationDTO], paragraphs: list[str]
    ) -> ApaValidationResultDTO:
        violations = self._apa_validator.validate_all_citations(
            citations=citations, paragraphs=paragraphs
        )
        count = len(violations)
        return ApaValidationResultDTO(
            is_valid=(count == 0), violation_count=count, violations=violations
        )

    def _validate_structure(
        self,
        document_content: DocumentContentDTO,
        article_type: ArticleType,
        has_references: bool,
    ) -> StructureValidationResultDTO:
        return self._structure_validator.validate_structure(
            document_content=document_content,
            article_type=article_type,
            has_references=has_references,
        )
