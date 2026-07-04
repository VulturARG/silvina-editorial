from unittest import TestCase

from src.domain.dtos.document_content_dto import DocumentContentDTO
from src.domain.enums.article_type import ArticleType
from src.domain.enums.section_name import SectionName
from src.domain.structure.structure_validator import StructureValidator


def _make_document(paragraphs: list[str]) -> DocumentContentDTO:
    return DocumentContentDTO(word_count=0, char_count=0, paragraphs=paragraphs)


_SCIENTIFIC_ALL_SECTIONS = [
    s.value
    for s in [
        SectionName.SUMMARY,
        SectionName.INTRODUCTION,
        SectionName.METHODOLOGY,
        SectionName.RESULTS,
        SectionName.DISCUSSION,
        SectionName.CONCLUSIONS,
        SectionName.REFERENCES,
    ]
]


class TestStructureValidatorScientific(TestCase):
    def setUp(self):
        self.validator = StructureValidator()

    def test_all_7_sections_present_is_valid(self):
        doc = _make_document(_SCIENTIFIC_ALL_SECTIONS)
        present, missing = self.validator.validate(doc, ArticleType.SCIENTIFIC)
        self.assertEqual(missing, [])

    def test_inline_colon_format_headers_detected(self):
        paragraphs = [
            "resumen: Este artículo presenta un estudio exhaustivo sobre los efectos del cambio climático.",
            "introducción: Este trabajo analiza el fenómeno desde múltiples perspectivas.",
            "metodología: Se empleó un enfoque cuantitativo mixto.",
            "resultados: Los datos muestran una tendencia significativa.",
            "discusión: Los hallazgos coinciden con estudios previos.",
            "conclusiones: El estudio confirma la hipótesis planteada inicialmente.",
            "referencias: Autor, A. (2020). Título. Revista, 1(1), 1-10.",
        ]
        doc = _make_document(paragraphs)
        present, missing = self.validator.validate(doc, ArticleType.SCIENTIFIC)
        self.assertEqual(missing, [])

    def test_missing_resumen_is_invalid(self):
        paragraphs = [
            s.value
            for s in [
                SectionName.INTRODUCTION,
                SectionName.METHODOLOGY,
                SectionName.RESULTS,
                SectionName.DISCUSSION,
                SectionName.CONCLUSIONS,
                SectionName.REFERENCES,
            ]
        ]
        doc = _make_document(paragraphs)
        present, missing = self.validator.validate(doc, ArticleType.SCIENTIFIC)
        self.assertIn(SectionName.SUMMARY, missing)

    def test_returns_tuple_of_two_lists(self):
        doc = _make_document(_SCIENTIFIC_ALL_SECTIONS)
        result = self.validator.validate(doc, ArticleType.SCIENTIFIC)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        present, missing = result
        self.assertIsInstance(present, list)
        self.assertIsInstance(missing, list)

    def test_missing_sections_listed_correctly(self):
        paragraphs = [
            s.value
            for s in [
                SectionName.INTRODUCTION,
                SectionName.METHODOLOGY,
                SectionName.RESULTS,
            ]
        ]
        doc = _make_document(paragraphs)
        present, missing = self.validator.validate(doc, ArticleType.SCIENTIFIC)
        self.assertIn(SectionName.SUMMARY, missing)
        self.assertIn(SectionName.DISCUSSION, missing)
        self.assertIn(SectionName.CONCLUSIONS, missing)
        self.assertIn(SectionName.REFERENCES, missing)
