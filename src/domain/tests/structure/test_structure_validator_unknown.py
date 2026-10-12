from unittest import TestCase

from src.domain.dtos.document_content_dto import DocumentContentDTO
from src.domain.enums.article_type import ArticleType
from src.domain.structure.structure_validator import StructureValidator
from src.domain.tests.structure.structure_norms_builder_for_test import (
    build_structure_norms_for_test,
)


def _make_document(paragraphs: list[str]) -> DocumentContentDTO:
    return DocumentContentDTO(
        word_count=0,
        char_count=0,
        paragraphs=paragraphs,
    )


class TestStructureValidatorUnknown(TestCase):
    def setUp(self):
        self.validator = StructureValidator(
            max_header_length=100,
            structure_norms=build_structure_norms_for_test(),
        )

    def test_unknown_type_always_valid(self):
        doc = _make_document(["Cualquier párrafo"])
        present, missing = self.validator.validate(doc, ArticleType.UNKNOWN)
        self.assertEqual(missing, [])

    def test_unknown_missing_sections_is_empty(self):
        doc = _make_document([])
        present, missing = self.validator.validate(doc, ArticleType.UNKNOWN)
        self.assertEqual(missing, [])

    def test_unknown_with_no_sections_still_valid(self):
        doc = _make_document([])
        present, missing = self.validator.validate(doc, ArticleType.UNKNOWN)
        self.assertTrue(len(missing) == 0)
