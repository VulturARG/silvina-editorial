from src.domain.dtos.document_content_dto import DocumentContentDTO
from src.domain.dtos.structure_norms_dto import StructureNormsDTO
from src.domain.dtos.structure_validation_result_dto import StructureValidationResultDTO
from src.domain.enums.article_type import ArticleType
from src.domain.enums.section_name import SectionName
from src.domain.exceptions.document_errors import DocumentEmpty


class StructureValidator:
    """Domain service that validates the structural completeness of a document."""

    def __init__(self, max_header_length: int, structure_norms: StructureNormsDTO) -> None:
        """Store the maximum header length and the structure norms."""
        self._max_header_length = max_header_length
        self._structure_norms = structure_norms

    def validate(
        self,
        document_content: DocumentContentDTO,
        article_type: ArticleType,
    ) -> tuple[list[SectionName], list[SectionName]]:
        """Return (present_sections, missing_sections). Low-level primitive; prefer `validate_structure`."""
        required = self._get_required_sections(article_type)
        present = self._extract_present_sections(document_content.paragraphs)
        present_lower = [s.lower() for s in present]
        missing = [s for s in required if s.lower() not in present_lower]
        return present, missing

    def validate_structure(
        self,
        document_content: DocumentContentDTO,
        article_type: ArticleType,
        has_references: bool,
    ) -> StructureValidationResultDTO:
        """Validate structure, raising on empty documents and filtering non-blocking sections."""
        if not document_content.paragraphs:
            raise DocumentEmpty

        _, missing = self.validate(document_content=document_content, article_type=article_type)
        missing = [s for s in missing if s != SectionName.DEVELOPMENT]
        if has_references:
            missing = [s for s in missing if s != SectionName.REFERENCES]

        return StructureValidationResultDTO(
            is_valid=len(missing) == 0,
            missing_sections=[section.value for section in missing],
        )

    def _extract_present_sections(self, paragraphs: list[str]) -> list[SectionName]:
        """Detect canonical section names from a list of paragraph strings."""
        sections: list[SectionName] = []
        all_keywords = [
            kw for keywords in self._structure_norms.section_aliases.values() for kw in keywords
        ]

        for para in paragraphs:
            text_lower = para.lower().strip()
            is_short_header = len(text_lower) < self._max_header_length
            is_inline_header = any(
                text_lower.startswith(kw + ":") or text_lower.startswith(kw + " :")
                for kw in all_keywords
            )
            if not (is_short_header or is_inline_header):
                continue
            for section_name, aliases in self._structure_norms.section_aliases.items():
                if any(kw in text_lower for kw in aliases):
                    sections.append(section_name)
                    break

        return sections

    def _get_required_sections(self, article_type: ArticleType) -> list[SectionName]:
        """Look up required sections for the article type in structure norms."""
        return list(self._structure_norms.required_sections.get(article_type, ()))
