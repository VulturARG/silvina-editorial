from unittest import TestCase

from src.domain.dtos.citation_analysis_result_dto import CitationAnalysisResultDTO
from src.infrastructure.adapters.report.citation_match_rate_formatter import (
    CitationMatchRateFormatter,
)


class TestCitationMatchRateFormatter(TestCase):
    def setUp(self) -> None:
        self.formatter = CitationMatchRateFormatter()

    def test_format_returns_not_applicable_when_total_citations_is_zero(self) -> None:
        citations = CitationAnalysisResultDTO(
            total_citations=0,
            total_references=5,
            matched_count=0,
            unmatched_count=0,
        )

        result = self.formatter.format(citations=citations)

        self.assertEqual(result, "N/A")

    def test_format_calculates_and_formats_percentage_to_one_decimal_place(self) -> None:
        citations = CitationAnalysisResultDTO(
            total_citations=10,
            total_references=10,
            matched_count=8,
            unmatched_count=2,
        )

        result = self.formatter.format(citations=citations)

        self.assertEqual(result, "80.0%")

    def test_format_formats_fractional_percentage_correctly(self) -> None:
        citations = CitationAnalysisResultDTO(
            total_citations=3,
            total_references=5,
            matched_count=1,
            unmatched_count=2,
        )

        result = self.formatter.format(citations=citations)

        self.assertEqual(result, "33.3%")

    def test_format_returns_one_hundred_percent_when_all_match(self) -> None:
        citations = CitationAnalysisResultDTO(
            total_citations=5,
            total_references=5,
            matched_count=5,
            unmatched_count=0,
        )

        result = self.formatter.format(citations=citations)

        self.assertEqual(result, "100.0%")
