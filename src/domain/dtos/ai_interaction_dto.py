from dataclasses import dataclass

from src.domain.dtos.base_dto import BaseDTO
from src.domain.enums.ai_provider import AiProvider
from src.domain.enums.ai_purpose import AiPurpose
from src.domain.enums.execution_status import ExecutionStatus


@dataclass(frozen=True)
class AiInteractionDTO(BaseDTO):
    """Data transfer object representing an external AI interaction event."""

    analysis_id: str
    provider: AiProvider
    purpose: AiPurpose
    model_name: str
    input_payload: str
    output_payload: str
    duration_ms: float
    status: ExecutionStatus
