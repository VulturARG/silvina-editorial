from src.domain.dtos.structure_norms_dto import StructureNormsDTO
from src.domain.enums.article_type import ArticleType
from src.domain.enums.section_name import SectionName
from src.domain.exceptions.editorial_norms_errors import EditorialNormInvalid
from src.infrastructure.editorial_norms_value_resolver import (
    EditorialNormsValueResolver,
)

_SECTION_NAME_BY_VALUE = {section.value: section for section in SectionName}
_ARTICLE_TYPE_BY_VALUE = {
    article_type.value: article_type
    for article_type in ArticleType
    if article_type != ArticleType.UNKNOWN
}
_EXPECTED_ARTICLE_TYPES = (
    ArticleType.SCIENTIFIC,
    ArticleType.POPULAR_SCIENCE,
    ArticleType.OPINION,
)


class StructureNormsLoader:
    """Loads and validates structure norms from an editorial norms value resolver."""

    def __init__(self, resolver: EditorialNormsValueResolver) -> None:
        """Store the editorial norms value resolver."""
        self._resolver = resolver

    def load(self) -> StructureNormsDTO:
        """Resolve, validate, and return the structure norms DTO."""
        section_aliases = self._load_section_aliases()
        required_sections = self._load_required_sections(section_aliases)
        return StructureNormsDTO(
            required_sections=required_sections,
            section_aliases=section_aliases,
        )

    def _load_section_aliases(self) -> dict[SectionName, tuple[str, ...]]:
        raw_aliases = self._resolver.read_string_list_table("section_aliases")
        section_aliases: dict[SectionName, tuple[str, ...]] = {}
        for section_label, aliases in raw_aliases.items():
            section_name = _SECTION_NAME_BY_VALUE.get(section_label)
            if section_name is None:
                raise EditorialNormInvalid(
                    f"'{section_label}' in section [section_aliases] is not a valid section name."
                )
            cleaned_aliases: list[str] = []
            for alias in aliases:
                normalized_alias = alias.strip().lower()
                if normalized_alias not in cleaned_aliases:
                    cleaned_aliases.append(normalized_alias)
            section_aliases[section_name] = tuple(cleaned_aliases)
        return section_aliases

    def _load_required_sections(
        self, section_aliases: dict[SectionName, tuple[str, ...]]
    ) -> dict[ArticleType, tuple[SectionName, ...]]:
        raw_sections = self._resolver.read_string_list_table("required_sections")
        required_sections: dict[ArticleType, tuple[SectionName, ...]] = {}
        for article_label, section_labels in raw_sections.items():
            if article_label == ArticleType.UNKNOWN.value:
                raise EditorialNormInvalid(
                    f"'{article_label}' in section [required_sections] is not an allowed article type."
                )
            article_type = _ARTICLE_TYPE_BY_VALUE.get(article_label)
            if article_type is None:
                raise EditorialNormInvalid(
                    f"'{article_label}' in section [required_sections] is not a valid article type."
                )
            sections: list[SectionName] = []
            for section_label in section_labels:
                section_name = _SECTION_NAME_BY_VALUE.get(section_label)
                if section_name is None:
                    raise EditorialNormInvalid(
                        f"'{section_label}' in section [required_sections] for article type '{article_label}' is not a valid section name."
                    )
                if section_name not in section_aliases:
                    raise EditorialNormInvalid(
                        f"'{section_label}' in section [required_sections] has no defined aliases in [section_aliases]."
                    )
                sections.append(section_name)
            required_sections[article_type] = tuple(sections)

        for expected in _EXPECTED_ARTICLE_TYPES:
            if expected not in required_sections:
                raise EditorialNormInvalid(
                    f"'{expected.value}' in section [required_sections] is missing."
                )

        return required_sections
