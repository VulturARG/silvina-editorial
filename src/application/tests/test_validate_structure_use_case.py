from dataclasses import FrozenInstanceError
from unittest import TestCase
from unittest.mock import MagicMock

from src.domain.dtos.document_content_dto import DocumentContentDTO
from src.domain.enums.article_type import ArticleType
from src.domain.enums.section_name import SectionName
from src.domain.exceptions.document_errors import DocumentEmpty
from src.application.validate_structure_use_case import ValidateStructureUseCase


def _make_document(paragraphs: list[str]) -> DocumentContentDTO:
    return DocumentContentDTO(word_count=0, char_count=0, paragraphs=paragraphs)


class TestValidateStructureUseCase(TestCase):
    def setUp(self):
        self.mock_validator = MagicMock()
        self.use_case = ValidateStructureUseCase(validator=self.mock_validator)

    def test_empty_paragraphs_raises_document_empty(self):
        doc = _make_document([])
        with self.assertRaises(DocumentEmpty):
            self.use_case.execute(document_content=doc, article_type=ArticleType.SCIENTIFIC)
        self.mock_validator.validate.assert_not_called()

    def test_missing_referencias_preserved_when_has_references_false(self):
        doc = _make_document(["Introducción"])
        self.mock_validator.validate.return_value = (
            [SectionName.INTRODUCTION],
            [SectionName.REFERENCES],
        )
        result = self.use_case.execute(
            document_content=doc, article_type=ArticleType.OPINION, has_references=False
        )
        self.assertIn(SectionName.REFERENCES, result.missing_sections)
        self.assertFalse(result.is_valid)

    def test_missing_referencias_removed_when_has_references_true(self):
        doc = _make_document(["Introducción", "Conclusiones"])
        self.mock_validator.validate.return_value = (
            [SectionName.INTRODUCTION, SectionName.CONCLUSIONS],
            [SectionName.REFERENCES],
        )
        result = self.use_case.execute(
            document_content=doc, article_type=ArticleType.SCIENTIFIC, has_references=True
        )
        self.assertNotIn(SectionName.REFERENCES, result.missing_sections)
        self.assertTrue(result.is_valid)

    def test_development_always_removed_from_missing(self):
        doc = _make_document(["Introducción", "Conclusiones"])
        self.mock_validator.validate.return_value = (
            [SectionName.INTRODUCTION, SectionName.CONCLUSIONS],
            [SectionName.DEVELOPMENT],
        )
        result = self.use_case.execute(
            document_content=doc, article_type=ArticleType.POPULAR_SCIENCE
        )
        self.assertNotIn(SectionName.DEVELOPMENT, result.missing_sections)
        self.assertTrue(result.is_valid)

    def test_is_valid_true_when_all_missing_filtered_out(self):
        doc = _make_document(["Introducción", "Conclusiones"])
        self.mock_validator.validate.return_value = (
            [SectionName.INTRODUCTION, SectionName.CONCLUSIONS],
            [SectionName.REFERENCES, SectionName.DEVELOPMENT],
        )
        result = self.use_case.execute(
            document_content=doc, article_type=ArticleType.POPULAR_SCIENCE, has_references=True
        )
        self.assertEqual(result.missing_sections, [])
        self.assertTrue(result.is_valid)

    def test_result_is_frozen(self):
        doc = _make_document(["Introducción"])
        self.mock_validator.validate.return_value = (
            [SectionName.INTRODUCTION],
            [],
        )
        result = self.use_case.execute(document_content=doc, article_type=ArticleType.OPINION)
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            result.is_valid = False  # type: ignore[misc] — intentional: assigning to frozen dataclass to assert immutability

    def test_default_has_references_is_false(self):
        doc = _make_document(["Resumen"])
        self.mock_validator.validate.return_value = (
            [SectionName.SUMMARY],
            [SectionName.INTRODUCTION, SectionName.REFERENCES],
        )
        result = self.use_case.execute(document_content=doc, article_type=ArticleType.SCIENTIFIC)
        self.assertIn(SectionName.REFERENCES, result.missing_sections)
        self.assertIn(SectionName.INTRODUCTION, result.missing_sections)
