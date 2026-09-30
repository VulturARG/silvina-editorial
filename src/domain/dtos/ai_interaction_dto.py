from dataclasses import dataclass

from src.domain.dtos.base_dto import BaseDTO


@dataclass(frozen=True)
class AiInteractionDTO(BaseDTO):
    """Data transfer object representing an external AI interaction event."""

    analysis_id: str
    provider: str
    purpose: str
    model_name: str
    input_payload: str
    output_payload: str
    duration_ms: float
    status: str
