from unittest import TestCase

from src.domain.dtos.document_content_dto import DocumentContentDTO
from src.domain.enums.article_type import ArticleType
from src.domain.enums.section_name import SectionName
from src.domain.structure.structure_validator import StructureValidator


def _make_document(paragraphs: list[str]) -> DocumentContentDTO:
    return DocumentContentDTO(word_count=0, char_count=0, paragraphs=paragraphs)


_POPULAR_SCIENCE_ALL_SECTIONS = [
    s.value
    for s in [
        SectionName.SUMMARY,
        SectionName.INTRODUCTION,
        SectionName.DEVELOPMENT,
        SectionName.CONCLUSIONS,
        SectionName.REFERENCES,
    ]
]


class TestStructureValidatorPopularScience(TestCase):
    def setUp(self):
        self.validator = StructureValidator()

    def test_all_popular_science_sections_present_is_valid(self):
        doc = _make_document(_POPULAR_SCIENCE_ALL_SECTIONS)
        present, missing = self.validator.validate(doc, ArticleType.POPULAR_SCIENCE)
        self.assertEqual(missing, [])

    def test_missing_desarrollo_is_invalid(self):
        paragraphs = [
            s.value
            for s in [
                SectionName.SUMMARY,
                SectionName.INTRODUCTION,
                SectionName.CONCLUSIONS,
                SectionName.REFERENCES,
            ]
        ]
        doc = _make_document(paragraphs)
        present, missing = self.validator.validate(doc, ArticleType.POPULAR_SCIENCE)
        self.assertIn(SectionName.DEVELOPMENT, missing)

    def test_missing_resumen_is_invalid(self):
        paragraphs = [
            s.value
            for s in [
                SectionName.INTRODUCTION,
                SectionName.DEVELOPMENT,
                SectionName.CONCLUSIONS,
                SectionName.REFERENCES,
            ]
        ]
        doc = _make_document(paragraphs)
        present, missing = self.validator.validate(doc, ArticleType.POPULAR_SCIENCE)
        self.assertIn(SectionName.SUMMARY, missing)

    def test_valid_when_all_5_sections_present(self):
        doc = _make_document(_POPULAR_SCIENCE_ALL_SECTIONS)
        present, missing = self.validator.validate(doc, ArticleType.POPULAR_SCIENCE)
        self.assertEqual(len(missing), 0)
