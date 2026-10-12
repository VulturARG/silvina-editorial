from dataclasses import dataclass

from src.domain.dtos.base_dto import BaseDTO
from src.domain.enums.article_type import ArticleType
from src.domain.enums.section_name import SectionName


@dataclass(frozen=True)
class StructureNormsDTO(BaseDTO):
    """Container for required sections per article type and canonical section aliases."""

    required_sections: dict[ArticleType, tuple[SectionName, ...]]
    section_aliases: dict[SectionName, tuple[str, ...]]
