from dataclasses import FrozenInstanceError
from unittest import TestCase

from src.domain.dtos.abstract_norms_dto import AbstractNormsDTO
from src.domain.dtos.caption_norms_dto import CaptionNormsDTO
from src.domain.dtos.document_format_norms_dto import DocumentFormatNormsDTO
from src.domain.dtos.editorial_norms_dto import EditorialNormsDTO
from src.domain.dtos.keyword_norms_dto import KeywordNormsDTO


class TestDocumentFormatNormsDTO(TestCase):
    def test_is_immutable(self):
        dto = DocumentFormatNormsDTO(
            margin_cm=2.5,
            margin_tolerance_cm=0.3,
            font_size_pt=12.0,
            font_size_tolerance_pt=1.0,
            allowed_fonts=("Times New Roman", "Arial"),
            max_unjustified_paragraph_ratio=0.3,
        )
        field_name = "margin_cm"
        with self.assertRaises(FrozenInstanceError):
            setattr(dto, field_name, 3.0)

    def test_as_dict_returns_plain_dictionary(self):
        dto = DocumentFormatNormsDTO(
            margin_cm=2.5,
            margin_tolerance_cm=0.3,
            font_size_pt=12.0,
            font_size_tolerance_pt=1.0,
            allowed_fonts=("Times New Roman", "Arial"),
            max_unjustified_paragraph_ratio=0.3,
        )
        self.assertEqual(
            dto.as_dict(),
            {
                "margin_cm": 2.5,
                "margin_tolerance_cm": 0.3,
                "font_size_pt": 12.0,
                "font_size_tolerance_pt": 1.0,
                "allowed_fonts": ("Times New Roman", "Arial"),
                "max_unjustified_paragraph_ratio": 0.3,
            },
        )

    def test_equality_based_on_field_values(self):
        first = DocumentFormatNormsDTO(
            margin_cm=2.5,
            margin_tolerance_cm=0.3,
            font_size_pt=12.0,
            font_size_tolerance_pt=1.0,
            allowed_fonts=("Times New Roman",),
            max_unjustified_paragraph_ratio=0.3,
        )
        second = DocumentFormatNormsDTO(
            margin_cm=2.5,
            margin_tolerance_cm=0.3,
            font_size_pt=12.0,
            font_size_tolerance_pt=1.0,
            allowed_fonts=("Times New Roman",),
            max_unjustified_paragraph_ratio=0.3,
        )
        third = DocumentFormatNormsDTO(
            margin_cm=3.0,
            margin_tolerance_cm=0.3,
            font_size_pt=12.0,
            font_size_tolerance_pt=1.0,
            allowed_fonts=("Times New Roman",),
            max_unjustified_paragraph_ratio=0.3,
        )
        self.assertEqual(first, second)
        self.assertNotEqual(first, third)


class TestCaptionNormsDTO(TestCase):
    def test_is_immutable(self):
        dto = CaptionNormsDTO(caption_prefixes=("figura", "fig."))
        field_name = "caption_prefixes"
        with self.assertRaises(FrozenInstanceError):
            setattr(dto, field_name, ("tabla",))

    def test_as_dict_returns_plain_dictionary(self):
        dto = CaptionNormsDTO(caption_prefixes=("figura", "fig."))
        self.assertEqual(dto.as_dict(), {"caption_prefixes": ("figura", "fig.")})

    def test_equality_based_on_field_values(self):
        first = CaptionNormsDTO(caption_prefixes=("figura",))
        second = CaptionNormsDTO(caption_prefixes=("figura",))
        third = CaptionNormsDTO(caption_prefixes=("tabla",))
        self.assertEqual(first, second)
        self.assertNotEqual(first, third)


class TestAbstractNormsDTO(TestCase):
    def test_is_immutable(self):
        dto = AbstractNormsDTO(
            section_keywords=("resumen", "abstract"),
            min_word_count=100,
            max_word_count=300,
        )
        field_name = "min_word_count"
        with self.assertRaises(FrozenInstanceError):
            setattr(dto, field_name, 150)

    def test_as_dict_returns_plain_dictionary(self):
        dto = AbstractNormsDTO(
            section_keywords=("resumen", "abstract"),
            min_word_count=100,
            max_word_count=300,
        )
        self.assertEqual(
            dto.as_dict(),
            {
                "section_keywords": ("resumen", "abstract"),
                "min_word_count": 100,
                "max_word_count": 300,
            },
        )

    def test_equality_based_on_field_values(self):
        first = AbstractNormsDTO(
            section_keywords=("resumen",),
            min_word_count=100,
            max_word_count=300,
        )
        second = AbstractNormsDTO(
            section_keywords=("resumen",),
            min_word_count=100,
            max_word_count=300,
        )
        third = AbstractNormsDTO(
            section_keywords=("resumen",),
            min_word_count=150,
            max_word_count=300,
        )
        self.assertEqual(first, second)
        self.assertNotEqual(first, third)


class TestKeywordNormsDTO(TestCase):
    def test_is_immutable(self):
        dto = KeywordNormsDTO(
            section_markers=("palabras clave", "keywords"),
            min_count=3,
            max_count=5,
        )
        field_name = "min_count"
        with self.assertRaises(FrozenInstanceError):
            setattr(dto, field_name, 4)

    def test_as_dict_returns_plain_dictionary(self):
        dto = KeywordNormsDTO(
            section_markers=("palabras clave", "keywords"),
            min_count=3,
            max_count=5,
        )
        self.assertEqual(
            dto.as_dict(),
            {
                "section_markers": ("palabras clave", "keywords"),
                "min_count": 3,
                "max_count": 5,
            },
        )

    def test_equality_based_on_field_values(self):
        first = KeywordNormsDTO(
            section_markers=("keywords",),
            min_count=3,
            max_count=5,
        )
        second = KeywordNormsDTO(
            section_markers=("keywords",),
            min_count=3,
            max_count=5,
        )
        third = KeywordNormsDTO(
            section_markers=("keywords",),
            min_count=2,
            max_count=5,
        )
        self.assertEqual(first, second)
        self.assertNotEqual(first, third)


class TestEditorialNormsDTO(TestCase):
    def test_is_immutable(self):
        dto = EditorialNormsDTO(
            document_format=DocumentFormatNormsDTO(
                margin_cm=2.5,
                margin_tolerance_cm=0.3,
                font_size_pt=12.0,
                font_size_tolerance_pt=1.0,
                allowed_fonts=("Arial",),
                max_unjustified_paragraph_ratio=0.3,
            ),
            figure_captions=CaptionNormsDTO(caption_prefixes=("figura",)),
            table_captions=CaptionNormsDTO(caption_prefixes=("tabla",)),
            abstract=AbstractNormsDTO(
                section_keywords=("resumen",),
                min_word_count=100,
                max_word_count=300,
            ),
            keywords=KeywordNormsDTO(
                section_markers=("keywords",),
                min_count=3,
                max_count=5,
            ),
        )
        field_name = "document_format"
        with self.assertRaises(FrozenInstanceError):
            setattr(dto, field_name, None)

    def test_as_dict_returns_nested_dictionary(self):
        dto = EditorialNormsDTO(
            document_format=DocumentFormatNormsDTO(
                margin_cm=2.5,
                margin_tolerance_cm=0.3,
                font_size_pt=12.0,
                font_size_tolerance_pt=1.0,
                allowed_fonts=("Arial",),
                max_unjustified_paragraph_ratio=0.3,
            ),
            figure_captions=CaptionNormsDTO(caption_prefixes=("figura",)),
            table_captions=CaptionNormsDTO(caption_prefixes=("tabla",)),
            abstract=AbstractNormsDTO(
                section_keywords=("resumen",),
                min_word_count=100,
                max_word_count=300,
            ),
            keywords=KeywordNormsDTO(
                section_markers=("keywords",),
                min_count=3,
                max_count=5,
            ),
        )
        expected = {
            "document_format": {
                "margin_cm": 2.5,
                "margin_tolerance_cm": 0.3,
                "font_size_pt": 12.0,
                "font_size_tolerance_pt": 1.0,
                "allowed_fonts": ("Arial",),
                "max_unjustified_paragraph_ratio": 0.3,
            },
            "figure_captions": {"caption_prefixes": ("figura",)},
            "table_captions": {"caption_prefixes": ("tabla",)},
            "abstract": {
                "section_keywords": ("resumen",),
                "min_word_count": 100,
                "max_word_count": 300,
            },
            "keywords": {
                "section_markers": ("keywords",),
                "min_count": 3,
                "max_count": 5,
            },
        }
        self.assertEqual(dto.as_dict(), expected)
