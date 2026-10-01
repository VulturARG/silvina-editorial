from dataclasses import dataclass

from src.domain.dtos.base_dto import BaseDTO
from src.domain.enums.article_type import ArticleType
from src.domain.enums.execution_status import ExecutionStatus
from src.domain.enums.publication_verdict import PublicationVerdict


@dataclass(frozen=True)
class AnalysisCompletionDTO(BaseDTO):
    """Data transfer object representing the completion summary of an analysis."""

    analysis_id: str
    document_name: str
    word_count: int | None
    char_count: int | None
    article_type: ArticleType | None
    verdict: PublicationVerdict | None
    total_duration_ms: float
    status: ExecutionStatus
