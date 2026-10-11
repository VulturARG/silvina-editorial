from collections.abc import Callable
from datetime import datetime
from os.path import join

from src.application.export_report_use_case import ExportReportUseCase
from src.domain.report.report_export_port import ReportExportPort
from src.infrastructure.adapters.report.citation_match_rate_formatter import (
    CitationMatchRateFormatter,
)
from src.infrastructure.adapters.report.docx_feedback_block_writer import (
    DocxFeedbackBlockWriter,
)
from src.infrastructure.adapters.report.docx_labeled_paragraph_writer import (
    DocxLabeledParagraphWriter,
)
from src.infrastructure.adapters.report.docx_markdown_run_writer import (
    DocxMarkdownRunWriter,
)
from src.infrastructure.adapters.report.docx_report_adapter import DocxReportAdapter
from src.infrastructure.adapters.report.docx_report_settings import DocxReportSettings
from src.infrastructure.adapters.report.docx_section_heading_writer import (
    DocxSectionHeadingWriter,
)
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
        return DocxReportAdapter(
            docx_report_settings=docx_report_settings,
            markdown_run_writer=markdown_run_writer,
            feedback_block_writer=self._feedback_block_writer(
                markdown_run_writer=markdown_run_writer,
                docx_report_settings=docx_report_settings,
            ),
            section_heading_writer=self._section_heading_writer(
                docx_report_settings=docx_report_settings,
            ),
            labeled_paragraph_writer=self._labeled_paragraph_writer(),
            citation_match_rate_formatter=self._citation_match_rate_formatter(),
            clock=self._clock(),
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
