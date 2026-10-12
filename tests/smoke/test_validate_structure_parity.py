"""Smoke test: StructureValidator validates real sample documents correctly.

Exercises src.domain.structure.structure_validator.StructureValidator directly
against real sample documents, verifying the expected missing sections and
validity outcome for each article type. Mirrors the DEVELOPMENT-section
removal applied in AnalyzeDocumentUseCase._validate_structure().

Run with: python -m pytest tests/smoke/ -v
"""

from pathlib import Path
from unittest import TestCase

from src.domain.dtos.document_content_dto import DocumentContentDTO
from src.domain.enums.article_type import ArticleType
from src.domain.enums.section_name import SectionName
from src.domain.structure.structure_validator import StructureValidator
from src.domain.tests.structure.structure_norms_builder_for_test import (
    build_structure_norms_for_test,
)
from src.infrastructure.adapters.document.docx_text_adapter import DocxTextAdapter

DOCS = Path(__file__).parent.parent.parent / "docs" / "sample-documents"

_DOCUMENTS = [
    ("1. test_Científico.docx", ArticleType.SCIENTIFIC),
    ("2. test_divulgacion_v2.docx", ArticleType.POPULAR_SCIENCE),
    ("3. test_opinion_v2.docx", ArticleType.OPINION),
]


def _make_document_content(paragraphs: list[str]) -> DocumentContentDTO:
    return DocumentContentDTO(
        word_count=sum(len(p.split()) for p in paragraphs),
        char_count=sum(len(p) for p in paragraphs),
        paragraphs=paragraphs,
    )


class TestValidateStructureParity(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reader = DocxTextAdapter()
        cls.structure_validator = StructureValidator(
            max_header_length=100,
            structure_norms=build_structure_norms_for_test(),
        )

    def _validate(self, filename: str, article_type: ArticleType) -> tuple[bool, set]:
        paragraphs = self.reader.read_paragraphs(path=str(DOCS / filename))
        document_content = _make_document_content(paragraphs)
        _, missing = self.structure_validator.validate(
            document_content=document_content, article_type=article_type
        )
        missing = {s for s in missing if s != SectionName.DEVELOPMENT}
        return len(missing) == 0, missing

    def test_cientifico_missing_sections(self):
        is_valid, missing = self._validate(*_DOCUMENTS[0])
        self.assertEqual(
            missing,
            {SectionName.METHODOLOGY, SectionName.RESULTS, SectionName.DISCUSSION},
        )
        self.assertFalse(is_valid)

    def test_divulgacion_is_valid(self):
        is_valid, missing = self._validate(*_DOCUMENTS[1])
        self.assertEqual(missing, set())
        self.assertTrue(is_valid)

    def test_opinion_missing_sections(self):
        is_valid, missing = self._validate(*_DOCUMENTS[2])
        self.assertEqual(
            missing,
            {SectionName.INTRODUCTION, SectionName.ARGUMENTATION, SectionName.CONCLUSIONS},
        )
        self.assertFalse(is_valid)
