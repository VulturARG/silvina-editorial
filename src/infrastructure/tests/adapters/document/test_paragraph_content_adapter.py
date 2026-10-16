from unittest import TestCase
from unittest.mock import patch

from src.domain.exceptions.document_errors import DocumentEmpty
from src.infrastructure.adapters.document.paragraph_content_adapter import ParagraphContentAdapter

VALID_PARAGRAPHS = [
    "Effects of Climate Change on Biodiversity",
    "Jane Doe",
    "ABSTRACT",
    "This paper examines the effect of rising temperatures on species distribution.",
    "KEYWORDS: climate, biodiversity, ecosystem",
    "INTRODUCTION",
    "Climate change is one of the defining challenges of our era.",
]


class TestParagraphContentAdapter(TestCase):
    def setUp(self):
        self.adapter = ParagraphContentAdapter()

    def test_empty_list_raises_document_empty(self):
        with self.assertRaises(DocumentEmpty):
            self.adapter.extract(paragraphs=[])

    def test_whitespace_only_paragraphs_raises_document_empty(self):
        with self.assertRaises(DocumentEmpty):
            self.adapter.extract(paragraphs=["   ", "\t", ""])

    def test_valid_paragraphs_returns_empty_references(self):
        dto = self.adapter.extract(paragraphs=VALID_PARAGRAPHS)
        self.assertEqual(dto.references, [])

    def test_valid_paragraphs_populates_text_counts(self):
        dto = self.adapter.extract(paragraphs=VALID_PARAGRAPHS)
        self.assertGreater(dto.word_count, 0)
        self.assertGreater(dto.char_count, 0)
        self.assertGreater(dto.paragraph_count, 0)

    def test_extract_sections_called_exactly_once(self):
        with patch.object(
            self.adapter, "_extract_sections", wraps=self.adapter._extract_sections
        ) as mock_sections:
            self.adapter.extract(paragraphs=VALID_PARAGRAPHS)
            mock_sections.assert_called_once()

    def test_valid_paragraphs_populates_structured_fields(self):
        dto = self.adapter.extract(paragraphs=VALID_PARAGRAPHS)
        self.assertGreater(len(dto.keywords), 0)
        self.assertGreater(len(dto.sections), 0)
