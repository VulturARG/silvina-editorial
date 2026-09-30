from dataclasses import dataclass

from src.domain.dtos.base_dto import BaseDTO


@dataclass(frozen=True)
class AnalysisStartDTO(BaseDTO):
    """Data transfer object representing the start of an analysis."""

    analysis_id: str
    document_name: str
