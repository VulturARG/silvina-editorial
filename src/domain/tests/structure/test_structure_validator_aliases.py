from unittest import TestCase

from src.domain.dtos.document_content_dto import DocumentContentDTO
from src.domain.dtos.structure_norms_dto import StructureNormsDTO
from src.domain.enums.article_type import ArticleType
from src.domain.enums.section_name import SectionName
from src.domain.structure.structure_validator import StructureValidator
from src.domain.tests.structure.structure_norms_builder_for_test import (
    build_structure_norms_for_test,
)


def _make_document(paragraphs: list[str]) -> DocumentContentDTO:
    return DocumentContentDTO(word_count=0, char_count=0, paragraphs=paragraphs)


class TestStructureValidatorAliases(TestCase):
    def setUp(self):
        self.validator = StructureValidator(
            max_header_length=100,
            structure_norms=build_structure_norms_for_test(),
        )

    def test_english_alias_abstract_maps_to_resumen(self):
        present = self.validator._extract_present_sections(["Abstract"])
        self.assertIn(SectionName.SUMMARY, present)

    def test_multiple_aliases_detected(self):
        paragraphs = ["Metodologia", "Methodology", "Discussion", "Results"]
        present = self.validator._extract_present_sections(paragraphs)
        self.assertIn(SectionName.METHODOLOGY, present)
        self.assertIn(SectionName.DISCUSSION, present)
        self.assertIn(SectionName.RESULTS, present)

    def test_fuentes_bibliograficas_maps_to_referencias(self):
        present = self.validator._extract_present_sections(["Fuentes bibliográficas"])
        self.assertIn(SectionName.REFERENCES, present)

    def test_long_body_text_not_detected_as_header(self):
        present = self.validator._extract_present_sections(["x" * 100])
        self.assertEqual(present, [])

    def test_short_header_under_100_chars_detected(self):
        present = self.validator._extract_present_sections([SectionName.INTRODUCTION.value])
        self.assertIn(SectionName.INTRODUCTION, present)

    def test_inline_colon_keyword_detected_regardless_of_length(self):
        long_inline = "resumen: " + "x" * 95
        present = self.validator._extract_present_sections([long_inline])
        self.assertIn(SectionName.SUMMARY, present)

    def test_inline_keyword_with_space_before_colon_detected(self):
        present = self.validator._extract_present_sections(
            ["resumen : Este es el resumen del artículo"]
        )
        self.assertIn(SectionName.SUMMARY, present)

    def test_introduccion_without_accent_detected(self):
        present = self.validator._extract_present_sections(["introduccion"])
        self.assertIn(SectionName.INTRODUCTION, present)

    def test_custom_max_header_length_rejects_paragraph_over_custom_threshold(self):
        validator = StructureValidator(
            max_header_length=50,
            structure_norms=build_structure_norms_for_test(),
        )
        long_paragraph = "Introducción de nuevas metodologías en el campo de la ciencia"
        self.assertEqual(len(long_paragraph), 61)
        present = validator._extract_present_sections([long_paragraph])
        self.assertEqual(present, [])

    def test_custom_max_header_length_accepts_short_paragraph_under_custom_threshold(self):
        validator = StructureValidator(
            max_header_length=50,
            structure_norms=build_structure_norms_for_test(),
        )
        present = validator._extract_present_sections([SectionName.INTRODUCTION.value])
        self.assertIn(SectionName.INTRODUCTION, present)

    def test_validator_detects_custom_injected_alias(self):
        custom_norms = StructureNormsDTO(
            required_sections={ArticleType.SCIENTIFIC: (SectionName.SUMMARY,)},
            section_aliases={SectionName.SUMMARY: ("resumen", "sinopsis")},
        )
        validator = StructureValidator(max_header_length=100, structure_norms=custom_norms)
        present = validator._extract_present_sections(["Sinopsis del documento"])
        self.assertIn(SectionName.SUMMARY, present)

    def test_validator_respects_custom_required_sections(self):
        custom_norms = StructureNormsDTO(
            required_sections={ArticleType.OPINION: (SectionName.SUMMARY,)},
            section_aliases={SectionName.SUMMARY: ("resumen",)},
        )
        validator = StructureValidator(max_header_length=100, structure_norms=custom_norms)
        doc = _make_document(["Introducción"])
        present, missing = validator.validate(doc, ArticleType.OPINION)
        self.assertEqual(missing, [SectionName.SUMMARY])
