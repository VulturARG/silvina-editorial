from unittest import TestCase

from src.domain.dtos.document_content_dto import DocumentContentDTO
from src.domain.enums.article_type import ArticleType
from src.domain.enums.section_name import SectionName
from src.domain.structure.structure_validator import StructureValidator
from src.domain.tests.structure.structure_norms_builder_for_test import (
    build_structure_norms_for_test,
)


class TestStructureValidatorMissingSectionLabels(TestCase):
    def setUp(self):
        self.validator = StructureValidator(
            max_header_length=100,
            structure_norms=build_structure_norms_for_test(),
        )
        paragraphs = [SectionName.INTRODUCTION.value, SectionName.ARGUMENTATION.value]
        self.document_content = DocumentContentDTO(
            word_count=0, char_count=0, paragraphs=paragraphs
        )

    def test_missing_sections_are_plain_text_labels(self):
        result = self.validator.validate_structure(
            document_content=self.document_content,
            article_type=ArticleType.OPINION,
            has_references=False,
        )
        self.assertEqual([type(section) for section in result.missing_sections], [str])

    def test_missing_section_renders_its_label_when_interpolated(self):
        result = self.validator.validate_structure(
            document_content=self.document_content,
            article_type=ArticleType.OPINION,
            has_references=False,
        )
        self.assertEqual(f"{result.missing_sections[0]}", "Conclusiones")
