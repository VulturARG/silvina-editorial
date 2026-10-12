from pathlib import Path

from src.domain.dtos.abstract_norms_dto import AbstractNormsDTO
from src.domain.dtos.caption_norms_dto import CaptionNormsDTO
from src.domain.dtos.document_format_norms_dto import DocumentFormatNormsDTO
from src.domain.dtos.editorial_norms_dto import EditorialNormsDTO
from src.domain.dtos.keyword_norms_dto import KeywordNormsDTO
from src.domain.exceptions.editorial_norms_errors import EditorialNormInvalid
from src.infrastructure.editorial_norms_toml_reader import EditorialNormsTomlReader
from src.infrastructure.editorial_norms_value_resolver import EditorialNormsValueResolver


class EditorialNormsLoader:
    """Loads and validates editorial norms from a TOML file into domain DTOs."""

    def __init__(self, editorial_norms_path: Path) -> None:
        """Store the path of the editorial norms file to read."""
        self._editorial_norms_path = Path(editorial_norms_path)

    def load(self) -> EditorialNormsDTO:
        """Read, resolve, validate, and return the complete editorial norms."""
        norms = EditorialNormsTomlReader(self._editorial_norms_path).load()
        resolver = EditorialNormsValueResolver(norms)

        margin_cm = resolver.read_float("document_format", "margin_cm")
        margin_tolerance_cm = resolver.read_float("document_format", "margin_tolerance_cm")
        font_size_pt = resolver.read_float("document_format", "font_size_pt")
        font_size_tolerance_pt = resolver.read_float("document_format", "font_size_tolerance_pt")
        allowed_fonts = resolver.read_string_list("document_format", "allowed_fonts")
        max_unjustified_paragraph_ratio = resolver.read_float(
            "document_format", "max_unjustified_paragraph_ratio"
        )

        self._validate_document_format(
            margin_cm=margin_cm,
            margin_tolerance_cm=margin_tolerance_cm,
            font_size_pt=font_size_pt,
            font_size_tolerance_pt=font_size_tolerance_pt,
            max_unjustified_paragraph_ratio=max_unjustified_paragraph_ratio,
        )

        figure_caption_prefixes = resolver.read_string_list("figures", "caption_prefixes")
        table_caption_prefixes = resolver.read_string_list("tables", "caption_prefixes")

        abstract_section_keywords = resolver.read_string_list("abstract", "section_keywords")
        abstract_min_word_count = resolver.read_integer("abstract", "min_word_count")
        abstract_max_word_count = resolver.read_integer("abstract", "max_word_count")
        self._validate_abstract_word_counts(
            min_word_count=abstract_min_word_count,
            max_word_count=abstract_max_word_count,
        )

        keyword_section_markers = resolver.read_string_list("keywords", "section_markers")
        keyword_min_count = resolver.read_integer("keywords", "min_count")
        keyword_max_count = resolver.read_integer("keywords", "max_count")
        self._validate_keyword_counts(
            min_count=keyword_min_count,
            max_count=keyword_max_count,
        )

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
        )

    def _validate_document_format(
        self,
        margin_cm: float,
        margin_tolerance_cm: float,
        font_size_pt: float,
        font_size_tolerance_pt: float,
        max_unjustified_paragraph_ratio: float,
    ) -> None:
        if margin_cm <= 0:
            raise EditorialNormInvalid(
                "'margin_cm' in section [document_format] must be greater than 0."
            )
        if margin_tolerance_cm < 0:
            raise EditorialNormInvalid(
                "'margin_tolerance_cm' in section [document_format] must be non-negative."
            )
        if font_size_pt <= 0:
            raise EditorialNormInvalid(
                "'font_size_pt' in section [document_format] must be greater than 0."
            )
        if font_size_tolerance_pt < 0:
            raise EditorialNormInvalid(
                "'font_size_tolerance_pt' in section [document_format] must be non-negative."
            )
        if not (0.0 <= max_unjustified_paragraph_ratio <= 1.0):
            raise EditorialNormInvalid(
                "'max_unjustified_paragraph_ratio' in section [document_format] must be between 0 and 1 inclusive."
            )

    def _validate_abstract_word_counts(self, min_word_count: int, max_word_count: int) -> None:
        if min_word_count < 1:
            raise EditorialNormInvalid("'min_word_count' in section [abstract] must be at least 1.")
        if min_word_count > max_word_count:
            raise EditorialNormInvalid(
                "'max_word_count' in section [abstract] must be greater than or equal to 'min_word_count'."
            )

    def _validate_keyword_counts(self, min_count: int, max_count: int) -> None:
        if min_count < 1:
            raise EditorialNormInvalid("'min_count' in section [keywords] must be at least 1.")
        if min_count > max_count:
            raise EditorialNormInvalid(
                "'max_count' in section [keywords] must be greater than or equal to 'min_count'."
            )
