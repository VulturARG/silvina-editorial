from dataclasses import FrozenInstanceError
from unittest import TestCase

from src.domain.dtos.structure_norms_dto import StructureNormsDTO
from src.domain.enums.article_type import ArticleType
from src.domain.enums.section_name import SectionName


class TestStructureNormsDTO(TestCase):
    def test_is_immutable(self):
        dto = StructureNormsDTO(
            required_sections={ArticleType.SCIENTIFIC: (SectionName.SUMMARY,)},
            section_aliases={SectionName.SUMMARY: ("resumen",)},
        )
        field_name = "required_sections"
        with self.assertRaises(FrozenInstanceError):
            setattr(dto, field_name, {})

    def test_as_dict_returns_plain_dictionary(self):
        dto = StructureNormsDTO(
            required_sections={ArticleType.SCIENTIFIC: (SectionName.SUMMARY,)},
            section_aliases={SectionName.SUMMARY: ("resumen",)},
        )
        self.assertEqual(
            dto.as_dict(),
            {
                "required_sections": {ArticleType.SCIENTIFIC: (SectionName.SUMMARY,)},
                "section_aliases": {SectionName.SUMMARY: ("resumen",)},
            },
        )

    def test_equality_based_on_field_values(self):
        first = StructureNormsDTO(
            required_sections={ArticleType.SCIENTIFIC: (SectionName.SUMMARY,)},
            section_aliases={SectionName.SUMMARY: ("resumen",)},
        )
        second = StructureNormsDTO(
            required_sections={ArticleType.SCIENTIFIC: (SectionName.SUMMARY,)},
            section_aliases={SectionName.SUMMARY: ("resumen",)},
        )
        third = StructureNormsDTO(
            required_sections={ArticleType.OPINION: (SectionName.INTRODUCTION,)},
            section_aliases={SectionName.INTRODUCTION: ("introducción",)},
        )
        self.assertEqual(first, second)
        self.assertNotEqual(first, third)
