from src.domain.dtos.abstract_norms_dto import AbstractNormsDTO
from src.domain.dtos.article_length_norms_dto import ArticleLengthNormsDTO
from src.domain.dtos.bibliography_norms_dto import BibliographyNormsDTO
from src.domain.dtos.caption_norms_dto import CaptionNormsDTO
from src.domain.dtos.document_format_norms_dto import DocumentFormatNormsDTO
from src.domain.dtos.editorial_norms_dto import EditorialNormsDTO
from src.domain.dtos.keyword_norms_dto import KeywordNormsDTO
from src.domain.dtos.structure_norms_dto import StructureNormsDTO
from src.domain.tests.structure.structure_norms_builder_for_test import (
    build_structure_norms_for_test,
)


def build_editorial_norms_for_test(
    margin_cm: float = 2.5,
    margin_tolerance_cm: float = 0.3,
    font_size_pt: float = 12.0,
    font_size_tolerance_pt: float = 1.0,
    allowed_fonts: tuple[str, ...] = ("Times New Roman", "Arial", "Calibri"),
    max_unjustified_paragraph_ratio: float = 0.3,
    figure_caption_prefixes: tuple[str, ...] = ("figura", "fig.", "figure"),
    table_caption_prefixes: tuple[str, ...] = ("tabla", "table", "cuadro"),
    abstract_section_keywords: tuple[str, ...] = ("resumen", "abstract", "síntesis", "sumario"),
    abstract_min_word_count: int = 100,
    abstract_max_word_count: int = 300,
    keyword_section_markers: tuple[str, ...] = (
        "palabras clave",
        "keywords",
        "key words",
        "descriptores",
    ),
    keyword_min_count: int = 3,
    keyword_max_count: int = 5,
    structure: StructureNormsDTO | None = None,
    bibliography_header_markers: tuple[str, ...] = ("refs", "biblio"),
    bibliography_header_max_length: int = 21,
    maximum_body_characters: int = 1234,
) -> EditorialNormsDTO:
    """Build an EditorialNormsDTO with test-owned values; any field can be overridden."""
    return EditorialNormsDTO(
        document_format=DocumentFormatNormsDTO(
            margin_cm=margin_cm,
            margin_tolerance_cm=margin_tolerance_cm,
            font_size_pt=font_size_pt,
            font_size_tolerance_pt=font_size_tolerance_pt,
            allowed_fonts=allowed_fonts,
            max_unjustified_paragraph_ratio=max_unjustified_paragraph_ratio,
        ),
        figure_captions=CaptionNormsDTO(caption_prefixes=figure_caption_prefixes),
        table_captions=CaptionNormsDTO(caption_prefixes=table_caption_prefixes),
        abstract=AbstractNormsDTO(
            section_keywords=abstract_section_keywords,
            min_word_count=abstract_min_word_count,
            max_word_count=abstract_max_word_count,
        ),
        keywords=KeywordNormsDTO(
            section_markers=keyword_section_markers,
            min_count=keyword_min_count,
            max_count=keyword_max_count,
        ),
        bibliography=BibliographyNormsDTO(
            header_markers=bibliography_header_markers,
            header_max_length=bibliography_header_max_length,
        ),
        article_length=ArticleLengthNormsDTO(max_body_chars=maximum_body_characters),
        structure=structure or build_structure_norms_for_test(),
    )
