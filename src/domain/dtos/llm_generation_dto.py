from dataclasses import dataclass

from src.domain.dtos.base_dto import BaseDTO


@dataclass(frozen=True)
class LlmGenerationDTO(BaseDTO):
    """Data transfer object representing language model generation text and usage metadata."""

    text: str
    prompt_tokens: int | None
    completion_tokens: int | None
    done_reason: str | None
