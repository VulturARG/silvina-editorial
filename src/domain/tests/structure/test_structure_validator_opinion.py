from unittest import TestCase

from src.domain.dtos.document_content_dto import DocumentContentDTO
from src.domain.enums.article_type import ArticleType
from src.domain.enums.section_name import SectionName
from src.domain.structure.structure_validator import StructureValidator
from src.domain.tests.structure.structure_norms_builder_for_test import (
    build_structure_norms_for_test,
)


def _make_document(paragraphs: list[str]) -> DocumentContentDTO:
    return DocumentContentDTO(word_count=0, char_count=0, paragraphs=paragraphs)


_OPINION_ALL_SECTIONS = [
    s.value
    for s in [
        SectionName.INTRODUCTION,
        SectionName.ARGUMENTATION,
        SectionName.CONCLUSIONS,
    ]
]


class TestStructureValidatorOpinion(TestCase):
    def setUp(self):
        self.validator = StructureValidator(
            max_header_length=100,
            structure_norms=build_structure_norms_for_test(),
        )

    def test_all_opinion_sections_present_is_valid(self):
        doc = _make_document(_OPINION_ALL_SECTIONS)
        present, missing = self.validator.validate(doc, ArticleType.OPINION)
        self.assertEqual(missing, [])

    def test_missing_argumentacion_is_invalid(self):
        paragraphs = [s.value for s in [SectionName.INTRODUCTION, SectionName.CONCLUSIONS]]
        doc = _make_document(paragraphs)
        present, missing = self.validator.validate(doc, ArticleType.OPINION)
        self.assertIn(SectionName.ARGUMENTATION, missing)

    def test_missing_conclusiones_is_invalid(self):
        paragraphs = [s.value for s in [SectionName.INTRODUCTION, SectionName.ARGUMENTATION]]
        doc = _make_document(paragraphs)
        present, missing = self.validator.validate(doc, ArticleType.OPINION)
        self.assertIn(SectionName.CONCLUSIONS, missing)
