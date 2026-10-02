from dataclasses import dataclass

from src.domain.dtos.base_dto import BaseDTO
from src.domain.enums.analysis_stage import AnalysisStage


@dataclass(frozen=True)
class StageDurationDTO(BaseDTO):
    """Data transfer object representing the execution duration of an analysis stage."""

    analysis_id: str
    stage_name: AnalysisStage
    duration_ms: float
