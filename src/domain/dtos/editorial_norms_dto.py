from dataclasses import dataclass

from src.domain.dtos.abstract_norms_dto import AbstractNormsDTO
from src.domain.dtos.base_dto import BaseDTO
from src.domain.dtos.caption_norms_dto import CaptionNormsDTO
from src.domain.dtos.document_format_norms_dto import DocumentFormatNormsDTO
from src.domain.dtos.keyword_norms_dto import KeywordNormsDTO


@dataclass(frozen=True)
class EditorialNormsDTO(BaseDTO):
    """Root editorial norms container combining all editorial specifications."""

    document_format: DocumentFormatNormsDTO
    figure_captions: CaptionNormsDTO
    table_captions: CaptionNormsDTO
    abstract: AbstractNormsDTO
    keywords: KeywordNormsDTO
