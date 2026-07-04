# ruff: noqa: E402
"""
Smoke tests: parity between legacy StructureValidator and new ValidateStructureUseCase.

Legacy path:
    WordReader -> paragraphs -> LegacyValidator.validate_structure() -> StructureValidationResult
    + main.py:230: remove "Desarrollo" unconditionally from missing_sections

New path:
    WordReader -> paragraphs -> DocumentContent -> ValidateStructureUseCase.execute()
    (DEVELOPMENT removal is built into the use case)

Run with: python -m pytest tests/smoke/ -v
"""

import sys
from pathlib import Path
from unittest import TestCase

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from data_access.word_reader import WordReader
from business_logic.structure_validator import StructureValidator as LegacyValidator
from domain.enums import ArticleType as LegacyArticleType
from src.domain.dtos.document_content_dto import DocumentContentDTO
from src.domain.enums.article_type import ArticleType
from src.infrastructure.wirings.validate_structure_wiring import ValidateStructureWiring

DOCS = ROOT / "docs" / "sample-documents"

_DOCUMENTS = [
    ("1. test_Científico.docx", ArticleType.SCIENTIFIC, LegacyArticleType.CIENTIFICO),
    ("2. test_divulgacion_v2.docx", ArticleType.POPULAR_SCIENCE, LegacyArticleType.DIVULGACION),
    ("3. test_opinion_v2.docx", ArticleType.OPINION, LegacyArticleType.OPINION),
]


def _make_document_content(paragraphs: list[str]) -> DocumentContentDTO:
    return DocumentContentDTO(
        word_count=sum(len(p.split()) for p in paragraphs),
        char_count=sum(len(p) for p in paragraphs),
        paragraphs=paragraphs,
    )


def _legacy_filtered_missing(legacy_missing: list[str]) -> list[str]:
    return [s for s in legacy_missing if s != "Desarrollo"]


class TestValidateStructureParity(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reader = WordReader()
        cls.legacy = LegacyValidator()
        cls.use_case = ValidateStructureWiring().create_use_case()

    def _run(self, filename: str, new_type: ArticleType, legacy_type: LegacyArticleType):
        paragraphs = self.reader.read_word_document(str(DOCS / filename))
        doc = _make_document_content(paragraphs)
        legacy_result = self.legacy.validate_structure(doc, legacy_type)
        new_result = self.use_case.execute(doc, new_type, has_references=False)
        return legacy_result, new_result

    def test_cientifico_missing_sections_match(self):
        legacy, new = self._run(*_DOCUMENTS[0])
        legacy_filtered = _legacy_filtered_missing(legacy.missing_sections)
        self.assertEqual(set(new.missing_sections), set(legacy_filtered))

    def test_cientifico_is_valid_matches(self):
        legacy, new = self._run(*_DOCUMENTS[0])
        legacy_filtered = _legacy_filtered_missing(legacy.missing_sections)
        self.assertEqual(new.is_valid, len(legacy_filtered) == 0)

    def test_divulgacion_missing_sections_match(self):
        legacy, new = self._run(*_DOCUMENTS[1])
        legacy_filtered = _legacy_filtered_missing(legacy.missing_sections)
        self.assertEqual(set(new.missing_sections), set(legacy_filtered))

    def test_divulgacion_is_valid_matches(self):
        legacy, new = self._run(*_DOCUMENTS[1])
        legacy_filtered = _legacy_filtered_missing(legacy.missing_sections)
        self.assertEqual(new.is_valid, len(legacy_filtered) == 0)

    def test_opinion_missing_sections_match(self):
        legacy, new = self._run(*_DOCUMENTS[2])
        legacy_filtered = _legacy_filtered_missing(legacy.missing_sections)
        self.assertEqual(set(new.missing_sections), set(legacy_filtered))

    def test_opinion_is_valid_matches(self):
        legacy, new = self._run(*_DOCUMENTS[2])
        legacy_filtered = _legacy_filtered_missing(legacy.missing_sections)
        self.assertEqual(new.is_valid, len(legacy_filtered) == 0)
