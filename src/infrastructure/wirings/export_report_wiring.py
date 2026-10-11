from collections.abc import Callable
from datetime import datetime
from os.path import join

from src.application.export_report_use_case import ExportReportUseCase
from src.domain.report.report_export_port import ReportExportPort
from src.infrastructure.adapters.report.citation_match_rate_formatter import (
    CitationMatchRateFormatter,
)
from src.infrastructure.adapters.report.docx_apa_validation_section import (
    DocxApaValidationSection,
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
from src.infrastructure.adapters.report.docx_labeled_paragraph_writer import (
    DocxLabeledParagraphWriter,
)
from src.infrastructure.adapters.report.docx_markdown_run_writer import (
    DocxMarkdownRunWriter,
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
from src.infrastructure.env_config import EnvConfig
from src.infrastructure.resources.assets import ASSETS_DIR


class ExportReportWiring:
    """Factory for building a ready-to-use ExportReportUseCase."""

    def create_use_case(self) -> ExportReportUseCase:
        """Return an ExportReportUseCase wired to the Word report export adapter."""
        return ExportReportUseCase(report_export_port=self._report_export_port())

    def _report_export_port(self) -> ReportExportPort:
        docx_report_settings = self._docx_report_settings()
        markdown_run_writer = self._markdown_run_writer()
        section_heading_writer = self._section_heading_writer(
            docx_report_settings=docx_report_settings,
        )
        labeled_paragraph_writer = self._labeled_paragraph_writer()
        citation_match_rate_formatter = self._citation_match_rate_formatter()
        clock = self._clock()
        return DocxReportAdapter(
            docx_report_settings=docx_report_settings,
            clock=clock,
            title_page_section=self._title_page_section(
                docx_report_settings=docx_report_settings,
            ),
            executive_summary_section=self._executive_summary_section(
                docx_report_settings=docx_report_settings,
                section_heading_writer=section_heading_writer,
                citation_match_rate_formatter=citation_match_rate_formatter,
            ),
            document_info_section=self._document_info_section(
                docx_report_settings=docx_report_settings,
                section_heading_writer=section_heading_writer,
                labeled_paragraph_writer=labeled_paragraph_writer,
            ),
            classification_section=self._classification_section(
                section_heading_writer=section_heading_writer,
                labeled_paragraph_writer=labeled_paragraph_writer,
            ),
            quality_analysis_section=self._quality_analysis_section(
                docx_report_settings=docx_report_settings,
                section_heading_writer=section_heading_writer,
                labeled_paragraph_writer=labeled_paragraph_writer,
                markdown_run_writer=markdown_run_writer,
                feedback_block_writer=self._feedback_block_writer(
                    markdown_run_writer=markdown_run_writer,
                    docx_report_settings=docx_report_settings,
                ),
            ),
            editorial_suitability_section=self._editorial_suitability_section(
                section_heading_writer=section_heading_writer,
                labeled_paragraph_writer=labeled_paragraph_writer,
            ),
            grammar_analysis_section=self._grammar_analysis_section(
                docx_report_settings=docx_report_settings,
                section_heading_writer=section_heading_writer,
                labeled_paragraph_writer=labeled_paragraph_writer,
            ),
            apa_validation_section=self._apa_validation_section(
                docx_report_settings=docx_report_settings,
                section_heading_writer=section_heading_writer,
            ),
            structure_validation_section=self._structure_validation_section(
                docx_report_settings=docx_report_settings,
                section_heading_writer=section_heading_writer,
            ),
            citations_analysis_section=self._citations_analysis_section(
                docx_report_settings=docx_report_settings,
                section_heading_writer=section_heading_writer,
                citation_match_rate_formatter=citation_match_rate_formatter,
            ),
            recommendations_section=self._recommendations_section(
                docx_report_settings=docx_report_settings,
                section_heading_writer=section_heading_writer,
            ),
            footer_section=self._footer_section(
                docx_report_settings=docx_report_settings,
                clock=clock,
            ),
            logo_path=join(ASSETS_DIR, "logo.jpg"),
        )

    def _docx_report_settings(self) -> DocxReportSettings:
        env_config = EnvConfig()
        return DocxReportSettings(
            app_name=env_config.silvina_app_name,
            app_version=env_config.silvina_version,
            score_high_threshold=env_config.report_score_high_threshold,
            score_medium_threshold=env_config.report_score_medium_threshold,
            words_per_page=env_config.report_words_per_page,
            max_errors_displayed=env_config.report_max_errors_displayed,
            context_truncation_limit=env_config.report_context_truncation_limit,
            max_replacements=env_config.report_max_replacements,
        )

    def _markdown_run_writer(self) -> DocxMarkdownRunWriter:
        return DocxMarkdownRunWriter()

    def _feedback_block_writer(
        self,
        markdown_run_writer: DocxMarkdownRunWriter,
        docx_report_settings: DocxReportSettings,
    ) -> DocxFeedbackBlockWriter:
        return DocxFeedbackBlockWriter(
            markdown_run_writer=markdown_run_writer,
            docx_report_settings=docx_report_settings,
        )

    def _section_heading_writer(
        self,
        docx_report_settings: DocxReportSettings,
    ) -> DocxSectionHeadingWriter:
        return DocxSectionHeadingWriter(docx_report_settings=docx_report_settings)

    def _labeled_paragraph_writer(self) -> DocxLabeledParagraphWriter:
        return DocxLabeledParagraphWriter()

    def _citation_match_rate_formatter(self) -> CitationMatchRateFormatter:
        return CitationMatchRateFormatter()

    def _clock(self) -> Callable[[], datetime]:
        return datetime.now

    def _title_page_section(
        self,
        docx_report_settings: DocxReportSettings,
    ) -> DocxReportSection:
        return DocxTitlePageSection(docx_report_settings=docx_report_settings)

    def _executive_summary_section(
        self,
        docx_report_settings: DocxReportSettings,
        section_heading_writer: DocxSectionHeadingWriter,
        citation_match_rate_formatter: CitationMatchRateFormatter,
    ) -> DocxReportSection:
        return DocxExecutiveSummarySection(
            docx_report_settings=docx_report_settings,
            section_heading_writer=section_heading_writer,
            citation_match_rate_formatter=citation_match_rate_formatter,
        )

    def _document_info_section(
        self,
        docx_report_settings: DocxReportSettings,
        section_heading_writer: DocxSectionHeadingWriter,
        labeled_paragraph_writer: DocxLabeledParagraphWriter,
    ) -> DocxReportSection:
        return DocxDocumentInfoSection(
            docx_report_settings=docx_report_settings,
            section_heading_writer=section_heading_writer,
            labeled_paragraph_writer=labeled_paragraph_writer,
        )

    def _classification_section(
        self,
        section_heading_writer: DocxSectionHeadingWriter,
        labeled_paragraph_writer: DocxLabeledParagraphWriter,
    ) -> DocxReportSection:
        return DocxClassificationSection(
            section_heading_writer=section_heading_writer,
            labeled_paragraph_writer=labeled_paragraph_writer,
        )

    def _quality_analysis_section(
        self,
        docx_report_settings: DocxReportSettings,
        section_heading_writer: DocxSectionHeadingWriter,
        labeled_paragraph_writer: DocxLabeledParagraphWriter,
        markdown_run_writer: DocxMarkdownRunWriter,
        feedback_block_writer: DocxFeedbackBlockWriter,
    ) -> DocxReportSection:
        return DocxQualityAnalysisSection(
            docx_report_settings=docx_report_settings,
            section_heading_writer=section_heading_writer,
            labeled_paragraph_writer=labeled_paragraph_writer,
            markdown_run_writer=markdown_run_writer,
            feedback_block_writer=feedback_block_writer,
        )

    def _editorial_suitability_section(
        self,
        section_heading_writer: DocxSectionHeadingWriter,
        labeled_paragraph_writer: DocxLabeledParagraphWriter,
    ) -> DocxReportSection:
        return DocxEditorialSuitabilitySection(
            section_heading_writer=section_heading_writer,
            labeled_paragraph_writer=labeled_paragraph_writer,
        )

    def _grammar_analysis_section(
        self,
        docx_report_settings: DocxReportSettings,
        section_heading_writer: DocxSectionHeadingWriter,
        labeled_paragraph_writer: DocxLabeledParagraphWriter,
    ) -> DocxReportSection:
        return DocxGrammarAnalysisSection(
            docx_report_settings=docx_report_settings,
            section_heading_writer=section_heading_writer,
            labeled_paragraph_writer=labeled_paragraph_writer,
        )

    def _apa_validation_section(
        self,
        docx_report_settings: DocxReportSettings,
        section_heading_writer: DocxSectionHeadingWriter,
    ) -> DocxReportSection:
        return DocxApaValidationSection(
            docx_report_settings=docx_report_settings,
            section_heading_writer=section_heading_writer,
        )

    def _structure_validation_section(
        self,
        docx_report_settings: DocxReportSettings,
        section_heading_writer: DocxSectionHeadingWriter,
    ) -> DocxReportSection:
        return DocxStructureValidationSection(
            docx_report_settings=docx_report_settings,
            section_heading_writer=section_heading_writer,
        )

    def _citations_analysis_section(
        self,
        docx_report_settings: DocxReportSettings,
        section_heading_writer: DocxSectionHeadingWriter,
        citation_match_rate_formatter: CitationMatchRateFormatter,
    ) -> DocxReportSection:
        return DocxCitationsAnalysisSection(
            docx_report_settings=docx_report_settings,
            section_heading_writer=section_heading_writer,
            citation_match_rate_formatter=citation_match_rate_formatter,
        )

    def _recommendations_section(
        self,
        docx_report_settings: DocxReportSettings,
        section_heading_writer: DocxSectionHeadingWriter,
    ) -> DocxReportSection:
        return DocxRecommendationsSection(
            docx_report_settings=docx_report_settings,
            section_heading_writer=section_heading_writer,
        )

    def _footer_section(
        self,
        docx_report_settings: DocxReportSettings,
        clock: Callable[[], datetime],
    ) -> DocxReportSection:
        return DocxFooterSection(docx_report_settings=docx_report_settings, clock=clock)
