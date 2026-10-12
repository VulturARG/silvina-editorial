from dataclasses import dataclass

from src.domain.dtos.base_dto import BaseDTO


@dataclass(frozen=True)
class DocumentFormatNormsDTO(BaseDTO):
    """Editorial norms for document layout and typography."""

    margin_cm: float
    margin_tolerance_cm: float
    font_size_pt: float
    font_size_tolerance_pt: float
    allowed_fonts: tuple[str, ...]
    max_unjustified_paragraph_ratio: float
