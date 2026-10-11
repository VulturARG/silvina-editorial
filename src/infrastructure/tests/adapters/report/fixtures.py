from collections.abc import Callable
from datetime import datetime
from unittest.mock import MagicMock

from src.domain.dtos.publication_verdict_dto import PublicationVerdictDTO
from src.domain.dtos.report_input_dto import ReportInputDTO
from src.domain.enums.publication_verdict import PublicationVerdict
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

FIXED_CLOCK_TIME = datetime(2026, 1, 15, 10, 30)


class ReportFixtures:
    @staticmethod
    def make_adapter(
        logo_path: str | None = None,
        clock: Callable[[], datetime] | None = None,
        docx_report_settings: DocxReportSettings | None = None,
    ) -> DocxReportAdapter:
        settings = (
            docx_report_settings
            if docx_report_settings is not None
            else ReportFixtures.make_settings()
        )
        markdown_run_writer = DocxMarkdownRunWriter()
        return DocxReportAdapter(
            docx_report_settings=settings,
            markdown_run_writer=markdown_run_writer,
            feedback_block_writer=DocxFeedbackBlockWriter(
                markdown_run_writer=markdown_run_writer,
                docx_report_settings=settings,
            ),
            section_heading_writer=DocxSectionHeadingWriter(docx_report_settings=settings),
            labeled_paragraph_writer=DocxLabeledParagraphWriter(),
            citation_match_rate_formatter=CitationMatchRateFormatter(),
            clock=clock if clock is not None else ReportFixtures.fixed_clock,
            logo_path=logo_path,
        )

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
    def make_doc_content_mock(
        word_count: int = 2500, char_count: int = 12000, title: str = "Test"
    ) -> MagicMock:
        doc_content = MagicMock()
        doc_content.word_count = word_count
        doc_content.char_count = char_count
        doc_content.title = title
        doc_content.authors = "Test Author"
        return doc_content

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
            "document_content": ReportFixtures.make_doc_content_mock(),
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
