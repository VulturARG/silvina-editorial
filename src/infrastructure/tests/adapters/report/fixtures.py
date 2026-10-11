from collections.abc import Callable
from datetime import datetime
from unittest.mock import MagicMock

from src.domain.dtos.publication_verdict_dto import PublicationVerdictDTO
from src.domain.dtos.report_input_dto import ReportInputDTO
from src.domain.enums.publication_verdict import PublicationVerdict
from src.infrastructure.adapters.report.citation_match_rate_formatter import (
    CitationMatchRateFormatter,
)
from src.infrastructure.adapters.report.docx_apa_validation_section import (
    DocxApaValidationSection,
)
from src.infrastructure.adapters.report.docx_base_style_decoration import (
    DocxBaseStyleDecoration,
)
from src.infrastructure.adapters.report.docx_citations_analysis_section import (
    DocxCitationsAnalysisSection,
)
from src.infrastructure.adapters.report.docx_classification_section import (
    DocxClassificationSection,
)
from src.infrastructure.adapters.report.docx_document_info_section import (
    DocxDocumentInfoSection,
)
from src.infrastructure.adapters.report.docx_editorial_suitability_section import (
    DocxEditorialSuitabilitySection,
)
from src.infrastructure.adapters.report.docx_executive_summary_section import (
    DocxExecutiveSummarySection,
)
from src.infrastructure.adapters.report.docx_feedback_block_writer import (
    DocxFeedbackBlockWriter,
)
from src.infrastructure.adapters.report.docx_footer_section import DocxFooterSection
from src.infrastructure.adapters.report.docx_grammar_analysis_section import (
    DocxGrammarAnalysisSection,
)
from src.infrastructure.adapters.report.docx_header_logo_decoration import (
    DocxHeaderLogoDecoration,
)
from src.infrastructure.adapters.report.docx_labeled_paragraph_writer import (
    DocxLabeledParagraphWriter,
)
from src.infrastructure.adapters.report.docx_markdown_run_writer import (
    DocxMarkdownRunWriter,
)
from src.infrastructure.adapters.report.docx_page_decoration import DocxPageDecoration
from src.infrastructure.adapters.report.docx_page_number_decoration import (
    DocxPageNumberDecoration,
)
from src.infrastructure.adapters.report.docx_quality_analysis_section import (
    DocxQualityAnalysisSection,
)
from src.infrastructure.adapters.report.docx_recommendations_section import (
    DocxRecommendationsSection,
)
from src.infrastructure.adapters.report.docx_report_adapter import DocxReportAdapter
from src.infrastructure.adapters.report.docx_report_section import DocxReportSection
from src.infrastructure.adapters.report.docx_report_settings import DocxReportSettings
from src.infrastructure.adapters.report.docx_section_heading_writer import (
    DocxSectionHeadingWriter,
)
from src.infrastructure.adapters.report.docx_structure_validation_section import (
    DocxStructureValidationSection,
)
from src.infrastructure.adapters.report.docx_title_page_section import DocxTitlePageSection

FIXED_CLOCK_TIME = datetime(2026, 1, 15, 10, 30)


class ReportFixtures:
    @staticmethod
    def make_adapter(
        logo_path: str | None = None,
        clock: Callable[[], datetime] | None = None,
        docx_report_settings: DocxReportSettings | None = None,
    ) -> DocxReportAdapter:
        settings = ReportFixtures._settings_or_default(docx_report_settings)
        report_clock = clock if clock is not None else ReportFixtures.fixed_clock
        return ReportFixtures.make_adapter_with_sections(
            sections=ReportFixtures.make_sections(
                clock=report_clock, docx_report_settings=settings
            ),
            page_decorations=ReportFixtures.make_page_decorations(
                logo_path=logo_path, clock=report_clock, docx_report_settings=settings
            ),
        )

    @staticmethod
    def make_adapter_with_sections(
        sections: dict[str, DocxReportSection],
        page_decorations: dict[str, DocxPageDecoration] | None = None,
    ) -> DocxReportAdapter:
        decorations = (
            page_decorations
            if page_decorations is not None
            else ReportFixtures.make_page_decorations()
        )
        return DocxReportAdapter(
            base_style_decoration=decorations["base_style_decoration"],
            header_logo_decoration=decorations["header_logo_decoration"],
            page_number_decoration=decorations["page_number_decoration"],
            title_page_section=sections["title_page_section"],
            executive_summary_section=sections["executive_summary_section"],
            document_info_section=sections["document_info_section"],
            classification_section=sections["classification_section"],
            quality_analysis_section=sections["quality_analysis_section"],
            editorial_suitability_section=sections["editorial_suitability_section"],
            grammar_analysis_section=sections["grammar_analysis_section"],
            apa_validation_section=sections["apa_validation_section"],
            structure_validation_section=sections["structure_validation_section"],
            citations_analysis_section=sections["citations_analysis_section"],
            recommendations_section=sections["recommendations_section"],
            footer_section=sections["footer_section"],
        )

    @staticmethod
    def make_page_decorations(
        logo_path: str | None = None,
        clock: Callable[[], datetime] | None = None,
        docx_report_settings: DocxReportSettings | None = None,
    ) -> dict[str, DocxPageDecoration]:
        settings = ReportFixtures._settings_or_default(docx_report_settings)
        return {
            "base_style_decoration": ReportFixtures.make_base_style_decoration(settings),
            "header_logo_decoration": ReportFixtures.make_header_logo_decoration(
                logo_path, clock, settings
            ),
            "page_number_decoration": ReportFixtures.make_page_number_decoration(settings),
        }

    @staticmethod
    def make_base_style_decoration(
        docx_report_settings: DocxReportSettings | None = None,
    ) -> DocxBaseStyleDecoration:
        return DocxBaseStyleDecoration(
            docx_report_settings=ReportFixtures._settings_or_default(docx_report_settings)
        )

    @staticmethod
    def make_header_logo_decoration(
        logo_path: str | None = None,
        clock: Callable[[], datetime] | None = None,
        docx_report_settings: DocxReportSettings | None = None,
    ) -> DocxHeaderLogoDecoration:
        return DocxHeaderLogoDecoration(
            docx_report_settings=ReportFixtures._settings_or_default(docx_report_settings),
            clock=clock if clock is not None else ReportFixtures.fixed_clock,
            logo_path=logo_path,
        )

    @staticmethod
    def make_page_number_decoration(
        docx_report_settings: DocxReportSettings | None = None,
    ) -> DocxPageNumberDecoration:
        return DocxPageNumberDecoration(
            docx_report_settings=ReportFixtures._settings_or_default(docx_report_settings)
        )

    @staticmethod
    def make_sections(
        clock: Callable[[], datetime] | None = None,
        docx_report_settings: DocxReportSettings | None = None,
    ) -> dict[str, DocxReportSection]:
        settings = ReportFixtures._settings_or_default(docx_report_settings)
        return {
            "title_page_section": ReportFixtures.make_title_page_section(settings),
            "executive_summary_section": ReportFixtures.make_executive_summary_section(settings),
            "document_info_section": ReportFixtures.make_document_info_section(settings),
            "classification_section": ReportFixtures.make_classification_section(settings),
            "quality_analysis_section": ReportFixtures.make_quality_analysis_section(settings),
            "editorial_suitability_section": ReportFixtures.make_editorial_suitability_section(
                settings
            ),
            "grammar_analysis_section": ReportFixtures.make_grammar_analysis_section(settings),
            "apa_validation_section": ReportFixtures.make_apa_validation_section(settings),
            "structure_validation_section": ReportFixtures.make_structure_validation_section(
                settings
            ),
            "citations_analysis_section": ReportFixtures.make_citations_analysis_section(settings),
            "recommendations_section": ReportFixtures.make_recommendations_section(settings),
            "footer_section": ReportFixtures.make_footer_section(clock, settings),
        }

    @staticmethod
    def make_executive_summary_section(
        docx_report_settings: DocxReportSettings | None = None,
    ) -> DocxExecutiveSummarySection:
        settings = ReportFixtures._settings_or_default(docx_report_settings)
        return DocxExecutiveSummarySection(
            docx_report_settings=settings,
            section_heading_writer=DocxSectionHeadingWriter(docx_report_settings=settings),
            citation_match_rate_formatter=CitationMatchRateFormatter(),
        )

    @staticmethod
    def make_quality_analysis_section(
        docx_report_settings: DocxReportSettings | None = None,
    ) -> DocxQualityAnalysisSection:
        settings = ReportFixtures._settings_or_default(docx_report_settings)
        markdown_run_writer = DocxMarkdownRunWriter()
        return DocxQualityAnalysisSection(
            docx_report_settings=settings,
            section_heading_writer=DocxSectionHeadingWriter(docx_report_settings=settings),
            labeled_paragraph_writer=DocxLabeledParagraphWriter(),
            markdown_run_writer=markdown_run_writer,
            feedback_block_writer=DocxFeedbackBlockWriter(
                markdown_run_writer=markdown_run_writer,
                docx_report_settings=settings,
            ),
        )

    @staticmethod
    def make_grammar_analysis_section(
        docx_report_settings: DocxReportSettings | None = None,
    ) -> DocxGrammarAnalysisSection:
        settings = ReportFixtures._settings_or_default(docx_report_settings)
        return DocxGrammarAnalysisSection(
            docx_report_settings=settings,
            section_heading_writer=DocxSectionHeadingWriter(docx_report_settings=settings),
            labeled_paragraph_writer=DocxLabeledParagraphWriter(),
        )

    @staticmethod
    def make_apa_validation_section(
        docx_report_settings: DocxReportSettings | None = None,
    ) -> DocxApaValidationSection:
        settings = ReportFixtures._settings_or_default(docx_report_settings)
        return DocxApaValidationSection(
            docx_report_settings=settings,
            section_heading_writer=DocxSectionHeadingWriter(docx_report_settings=settings),
        )

    @staticmethod
    def make_recommendations_section(
        docx_report_settings: DocxReportSettings | None = None,
    ) -> DocxRecommendationsSection:
        settings = ReportFixtures._settings_or_default(docx_report_settings)
        return DocxRecommendationsSection(
            docx_report_settings=settings,
            section_heading_writer=DocxSectionHeadingWriter(docx_report_settings=settings),
        )

    @staticmethod
    def make_title_page_section(
        docx_report_settings: DocxReportSettings | None = None,
    ) -> DocxTitlePageSection:
        return DocxTitlePageSection(
            docx_report_settings=ReportFixtures._settings_or_default(docx_report_settings)
        )

    @staticmethod
    def make_document_info_section(
        docx_report_settings: DocxReportSettings | None = None,
    ) -> DocxDocumentInfoSection:
        settings = ReportFixtures._settings_or_default(docx_report_settings)
        return DocxDocumentInfoSection(
            docx_report_settings=settings,
            section_heading_writer=DocxSectionHeadingWriter(docx_report_settings=settings),
            labeled_paragraph_writer=DocxLabeledParagraphWriter(),
        )

    @staticmethod
    def make_classification_section(
        docx_report_settings: DocxReportSettings | None = None,
    ) -> DocxClassificationSection:
        settings = ReportFixtures._settings_or_default(docx_report_settings)
        return DocxClassificationSection(
            section_heading_writer=DocxSectionHeadingWriter(docx_report_settings=settings),
            labeled_paragraph_writer=DocxLabeledParagraphWriter(),
        )

    @staticmethod
    def make_editorial_suitability_section(
        docx_report_settings: DocxReportSettings | None = None,
    ) -> DocxEditorialSuitabilitySection:
        settings = ReportFixtures._settings_or_default(docx_report_settings)
        return DocxEditorialSuitabilitySection(
            section_heading_writer=DocxSectionHeadingWriter(docx_report_settings=settings),
            labeled_paragraph_writer=DocxLabeledParagraphWriter(),
        )

    @staticmethod
    def make_structure_validation_section(
        docx_report_settings: DocxReportSettings | None = None,
    ) -> DocxStructureValidationSection:
        settings = ReportFixtures._settings_or_default(docx_report_settings)
        return DocxStructureValidationSection(
            docx_report_settings=settings,
            section_heading_writer=DocxSectionHeadingWriter(docx_report_settings=settings),
        )

    @staticmethod
    def make_citations_analysis_section(
        docx_report_settings: DocxReportSettings | None = None,
    ) -> DocxCitationsAnalysisSection:
        settings = ReportFixtures._settings_or_default(docx_report_settings)
        return DocxCitationsAnalysisSection(
            docx_report_settings=settings,
            section_heading_writer=DocxSectionHeadingWriter(docx_report_settings=settings),
            citation_match_rate_formatter=CitationMatchRateFormatter(),
        )

    @staticmethod
    def make_footer_section(
        clock: Callable[[], datetime] | None = None,
        docx_report_settings: DocxReportSettings | None = None,
    ) -> DocxFooterSection:
        return DocxFooterSection(
            docx_report_settings=ReportFixtures._settings_or_default(docx_report_settings),
            clock=clock if clock is not None else ReportFixtures.fixed_clock,
        )

    @staticmethod
    def _settings_or_default(
        docx_report_settings: DocxReportSettings | None,
    ) -> DocxReportSettings:
        if docx_report_settings is not None:
            return docx_report_settings
        return ReportFixtures.make_settings()

    @staticmethod
    def fixed_clock() -> datetime:
        return FIXED_CLOCK_TIME

    @staticmethod
    def make_settings(**overrides) -> DocxReportSettings:
        defaults = {
            "app_name": "Silvina Editorial Assistant",
            "app_version": "0.9",
            "score_high_threshold": 8.0,
            "score_medium_threshold": 6.0,
            "words_per_page": 250,
            "max_errors_displayed": 5,
            "context_truncation_limit": 150,
            "max_replacements": 3,
        }
        defaults.update(overrides)
        return DocxReportSettings(**defaults)

    @staticmethod
    def make_grammar_mock(score: float = 7.5, errors: list | None = None) -> MagicMock:
        grammar = MagicMock()
        grammar.score = score
        grammar.feedback = "Good grammar"
        grammar.errors = errors if errors is not None else []
        return grammar

    @staticmethod
    def make_quality_mock(overall_score: float = 8.0) -> MagicMock:
        quality = MagicMock()
        quality.overall_score = overall_score
        quality.dimension_scores = {}
        return quality

    @staticmethod
    def make_citations_mock(total: int = 5, matched: int = 5, references: int = 5) -> MagicMock:
        citations = MagicMock()
        citations.total_citations = total
        citations.total_references = references
        citations.matched_count = matched
        return citations

    @staticmethod
    def make_apa_validation_mock(violations: list | None = None) -> MagicMock:
        apa = MagicMock()
        apa.violations = violations if violations is not None else []
        return apa

    @staticmethod
    def make_document_content_mock(
        word_count: int = 2500, char_count: int = 12000, title: str = "Test"
    ) -> MagicMock:
        document_content = MagicMock()
        document_content.word_count = word_count
        document_content.char_count = char_count
        document_content.title = title
        document_content.authors = "Test Author"
        return document_content

    @staticmethod
    def make_classification_mock(article_type_value: str = "Investigación") -> MagicMock:
        classification = MagicMock()
        classification.article_type.value = article_type_value
        classification.confidence = 0.9
        classification.reasoning = "Test reasoning"
        return classification

    @staticmethod
    def make_structure_mock(is_valid: bool = True) -> MagicMock:
        structure = MagicMock()
        structure.is_valid = is_valid
        structure.missing_sections = []
        return structure

    @staticmethod
    def make_verdict_dto(
        verdict: PublicationVerdict = PublicationVerdict.APPROVED,
    ) -> PublicationVerdictDTO:
        messages = {
            PublicationVerdict.APPROVED: "✅ APTO PARA PUBLICACIÓN. El documento cumple con los estándares de calidad.",
            PublicationVerdict.WARNING: "⚠️ REQUIERE REVISIÓN antes de publicación.",
            PublicationVerdict.CRITICAL: "❌ NO APTO PARA PUBLICACIÓN.",
        }
        return PublicationVerdictDTO(verdict=verdict, message=messages[verdict])

    @staticmethod
    def make_report_input_dto(**overrides) -> ReportInputDTO:
        defaults = {
            "filename": "test.docx",
            "document_content": ReportFixtures.make_document_content_mock(),
            "classification": ReportFixtures.make_classification_mock(),
            "quality": ReportFixtures.make_quality_mock(),
            "grammar": ReportFixtures.make_grammar_mock(),
            "structure": ReportFixtures.make_structure_mock(),
            "citations": ReportFixtures.make_citations_mock(),
            "apa_validation": ReportFixtures.make_apa_validation_mock(),
            "recommendations": [],
            "verdict": ReportFixtures.make_verdict_dto(),
            "eumic_violations": [],
        }
        defaults.update(overrides)
        return ReportInputDTO(**defaults)
