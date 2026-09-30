from dataclasses import dataclass

from src.domain.dtos.base_dto import BaseDTO


@dataclass(frozen=True)
class AnalysisCompletionDTO(BaseDTO):
    """Data transfer object representing the completion summary of an analysis."""

    analysis_id: str
    document_name: str
    word_count: int
    char_count: int
    article_type: str
    verdict: str
    total_duration_ms: float
    status: str
