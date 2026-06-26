from unittest import TestCase

from src.domain.dtos.document_content_dto import DocumentContentDTO
from src.domain.enums.extraction_fallback import ExtractionFallback


class TestDocumentContentDTODisplayAuthors(TestCase):
    def test_display_authors_returns_authors_when_set(self):
        document = DocumentContentDTO(word_count=10, char_count=50, authors="Jane Doe")
        self.assertEqual(document.display_authors, "Jane Doe")

    def test_display_authors_returns_fallback_when_authors_is_none(self):
        document = DocumentContentDTO(word_count=10, char_count=50, authors=None)
        self.assertEqual(document.display_authors, ExtractionFallback.UNKNOWN_AUTHOR)

    def test_display_authors_fallback_value_is_correct_string(self):
        document = DocumentContentDTO(word_count=10, char_count=50, authors=None)
        self.assertEqual(document.display_authors, "Autor no identificado")
