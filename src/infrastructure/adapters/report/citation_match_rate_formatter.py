from src.domain.dtos.citation_analysis_result_dto import CitationAnalysisResultDTO


class CitationMatchRateFormatter:
    """Format citation match rates for analysis reports."""

    def format(self, citations: CitationAnalysisResultDTO) -> str:
        """Format the match rate as a percentage or 'N/A' when citations are absent."""
        if citations.total_citations == 0:
            return "N/A"
        rate = citations.matched_count / citations.total_citations * 100
        return f"{rate:.1f}%"
