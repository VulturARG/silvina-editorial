from unittest import TestCase

from src.domain.document.article_body_locator import ArticleBodyLocator
from src.domain.document.article_header_locator import ArticleHeaderLocator
from src.domain.document.document_content_extractor import DocumentContentExtractor
from src.domain.document.table_markdown_renderer import TableMarkdownRenderer
from src.domain.dtos.character_count_dto import CharacterCountDTO
from src.domain.dtos.document_content_dto import DocumentContentDTO
from src.domain.dtos.reference_dto import ReferenceDTO
from src.domain.exceptions.count_errors import CharacterCountUnavailable
from src.domain.tests.document.fake_character_count_port import FakeCharacterCountPort
from src.domain.tests.document.fake_content_extraction_port import FakeContentExtractionPort
from src.domain.tests.document.fake_document_table_port import FakeDocumentTablePort
from src.domain.tests.document.fake_document_text_port import FakeDocumentTextPort
from src.domain.tests.document.fake_reference_extraction_port import FakeReferenceExtractionPort
from src.domain.tests.dtos.editorial_norms_builder_for_test import build_editorial_norms_for_test


class TestDocumentContentExtractor(TestCase):
    """Unit tests for DocumentContentExtractor."""

    def test_extract_content_returns_base_dto_when_counts_available(self):
        document_text_port = FakeDocumentTextPort(paragraphs=["Para 0", "Para 1"])
        base_document_content = DocumentContentDTO(
            word_count=1, char_count=1, paragraphs=["Para 0", "Para 0", "Para 1"]
        )
        content_extraction_port = FakeContentExtractionPort(result=base_document_content)
        character_counts = CharacterCountDTO(word_count=10, char_count=100, paragraph_count=2)
        character_count_port = FakeCharacterCountPort(result=character_counts)
        reference_extraction_port = FakeReferenceExtractionPort()

        document_content_extractor = DocumentContentExtractor(
            document_text_port=document_text_port,
            content_extraction_port=content_extraction_port,
            character_count_port=character_count_port,
            reference_extraction_port=reference_extraction_port,
            article_body_locator=self._build_article_body_locator(),
            article_header_locator=self._build_article_header_locator(),
            document_table_port=FakeDocumentTablePort(),
            table_markdown_renderer=TableMarkdownRenderer(),
        )
        document_content = document_content_extractor.extract_content(docx_path="test.docx")

        self.assertEqual(document_content.word_count, 10)
        self.assertEqual(document_content.char_count, 100)
        self.assertEqual(document_content.paragraph_count, 2)
        self.assertEqual(document_content.paragraphs, ["Para 0", "Para 0", "Para 1"])

    def test_extract_content_falls_back_to_base_when_character_count_unavailable(self):
        document_text_port = FakeDocumentTextPort(paragraphs=["Para 0"])
        base_document_content = DocumentContentDTO(
            word_count=1, char_count=1, paragraphs=["Para 0", "Para 0"]
        )
        content_extraction_port = FakeContentExtractionPort(result=base_document_content)
        character_count_port = FakeCharacterCountPort(error=CharacterCountUnavailable())
        reference_extraction_port = FakeReferenceExtractionPort()

        document_content_extractor = DocumentContentExtractor(
            document_text_port=document_text_port,
            content_extraction_port=content_extraction_port,
            character_count_port=character_count_port,
            reference_extraction_port=reference_extraction_port,
            article_body_locator=self._build_article_body_locator(),
            article_header_locator=self._build_article_header_locator(),
            document_table_port=FakeDocumentTablePort(),
            table_markdown_renderer=TableMarkdownRenderer(),
        )
        document_content = document_content_extractor.extract_content(docx_path="test.docx")

        self.assertEqual(document_content.word_count, base_document_content.word_count)
        self.assertEqual(document_content.char_count, base_document_content.char_count)
        self.assertEqual(document_content.paragraph_count, base_document_content.paragraph_count)
        self.assertEqual(document_content.paragraphs, base_document_content.paragraphs)
        self.assertEqual(document_content.references, [])

    def test_extract_content_falls_back_to_base_when_counts_is_none(self):
        document_text_port = FakeDocumentTextPort(paragraphs=["Para 0"])
        base_document_content = DocumentContentDTO(
            word_count=1, char_count=1, paragraphs=["Para 0", "Para 0"]
        )
        content_extraction_port = FakeContentExtractionPort(result=base_document_content)
        character_count_port = FakeCharacterCountPort(result=None)
        reference_extraction_port = FakeReferenceExtractionPort()

        document_content_extractor = DocumentContentExtractor(
            document_text_port=document_text_port,
            content_extraction_port=content_extraction_port,
            character_count_port=character_count_port,
            reference_extraction_port=reference_extraction_port,
            article_body_locator=self._build_article_body_locator(),
            article_header_locator=self._build_article_header_locator(),
            document_table_port=FakeDocumentTablePort(),
            table_markdown_renderer=TableMarkdownRenderer(),
        )
        document_content = document_content_extractor.extract_content(docx_path="test.docx")

        self.assertEqual(document_content.word_count, base_document_content.word_count)
        self.assertEqual(document_content.char_count, base_document_content.char_count)
        self.assertEqual(document_content.paragraph_count, base_document_content.paragraph_count)
        self.assertEqual(document_content.paragraphs, base_document_content.paragraphs)
        self.assertEqual(document_content.references, [])

    def test_extract_content_reads_paragraphs_and_passes_them_to_content_port(self):
        document_text_port = FakeDocumentTextPort(paragraphs=["Alpha", "Beta"])
        received_calls: list[tuple[list[str], str | None]] = []

        class RecordingContentExtractionPort(FakeContentExtractionPort):
            def extract(
                self, paragraphs: list[str], docx_path: str | None = None
            ) -> DocumentContentDTO:
                received_calls.append((paragraphs, docx_path))
                return super().extract(paragraphs, docx_path)

        content_extraction_port = RecordingContentExtractionPort(
            result=DocumentContentDTO(
                word_count=0, char_count=0, paragraphs=["Alpha", "Alpha", "Beta"]
            )
        )
        character_count_port = FakeCharacterCountPort(result=None)
        reference_extraction_port = FakeReferenceExtractionPort()

        document_content_extractor = DocumentContentExtractor(
            document_text_port=document_text_port,
            content_extraction_port=content_extraction_port,
            character_count_port=character_count_port,
            reference_extraction_port=reference_extraction_port,
            article_body_locator=self._build_article_body_locator(),
            article_header_locator=self._build_article_header_locator(),
            document_table_port=FakeDocumentTablePort(),
            table_markdown_renderer=TableMarkdownRenderer(),
        )
        document_content = document_content_extractor.extract_content(docx_path="test.docx")

        self.assertEqual(received_calls, [(["Alpha", "Beta"], "test.docx")])
        self.assertEqual(document_content.paragraphs, ["Alpha", "Alpha", "Beta"])

    def test_extract_content_populates_references_when_counts_available(self):
        document_text_port = FakeDocumentTextPort(paragraphs=["Paragraph text"])
        base_document_content = DocumentContentDTO(
            word_count=2, char_count=14, paragraphs=["Paragraph text", "Paragraph text"]
        )
        content_extraction_port = FakeContentExtractionPort(result=base_document_content)
        character_counts = CharacterCountDTO(word_count=20, char_count=140, paragraph_count=1)
        character_count_port = FakeCharacterCountPort(result=character_counts)
        references = [
            ReferenceDTO(text="Reference one text"),
            ReferenceDTO(text="Reference two text"),
        ]
        reference_extraction_port = FakeReferenceExtractionPort(result=(references, "Referencias"))

        document_content_extractor = DocumentContentExtractor(
            document_text_port=document_text_port,
            content_extraction_port=content_extraction_port,
            character_count_port=character_count_port,
            reference_extraction_port=reference_extraction_port,
            article_body_locator=self._build_article_body_locator(),
            article_header_locator=self._build_article_header_locator(),
            document_table_port=FakeDocumentTablePort(),
            table_markdown_renderer=TableMarkdownRenderer(),
        )
        document_content = document_content_extractor.extract_content(docx_path="test.docx")

        self.assertEqual(document_content.references, references)
        self.assertEqual(document_content.word_count, 20)
        self.assertEqual(document_content.char_count, 140)
        self.assertEqual(document_content.paragraph_count, 1)

    def test_extract_content_populates_references_when_character_count_unavailable(self):
        document_text_port = FakeDocumentTextPort(paragraphs=["Paragraph text"])
        base_document_content = DocumentContentDTO(
            word_count=2, char_count=14, paragraphs=["Paragraph text", "Paragraph text"]
        )
        content_extraction_port = FakeContentExtractionPort(result=base_document_content)
        character_count_port = FakeCharacterCountPort(error=CharacterCountUnavailable())
        references = [ReferenceDTO(text="Reference one text")]
        reference_extraction_port = FakeReferenceExtractionPort(result=(references, "Referencias"))

        document_content_extractor = DocumentContentExtractor(
            document_text_port=document_text_port,
            content_extraction_port=content_extraction_port,
            character_count_port=character_count_port,
            reference_extraction_port=reference_extraction_port,
            article_body_locator=self._build_article_body_locator(),
            article_header_locator=self._build_article_header_locator(),
            document_table_port=FakeDocumentTablePort(),
            table_markdown_renderer=TableMarkdownRenderer(),
        )
        document_content = document_content_extractor.extract_content(docx_path="test.docx")

        self.assertEqual(document_content.references, references)
        self.assertEqual(document_content.word_count, 2)
        self.assertEqual(document_content.char_count, 14)

    def test_extract_content_populates_references_when_counts_is_none(self):
        document_text_port = FakeDocumentTextPort(paragraphs=["Paragraph text"])
        base_document_content = DocumentContentDTO(
            word_count=2, char_count=14, paragraphs=["Paragraph text", "Paragraph text"]
        )
        content_extraction_port = FakeContentExtractionPort(result=base_document_content)
        character_count_port = FakeCharacterCountPort(result=None)
        references = [ReferenceDTO(text="Reference one text")]
        reference_extraction_port = FakeReferenceExtractionPort(result=(references, "Referencias"))

        document_content_extractor = DocumentContentExtractor(
            document_text_port=document_text_port,
            content_extraction_port=content_extraction_port,
            character_count_port=character_count_port,
            reference_extraction_port=reference_extraction_port,
            article_body_locator=self._build_article_body_locator(),
            article_header_locator=self._build_article_header_locator(),
            document_table_port=FakeDocumentTablePort(),
            table_markdown_renderer=TableMarkdownRenderer(),
        )
        document_content = document_content_extractor.extract_content(docx_path="test.docx")

        self.assertEqual(document_content.references, references)
        self.assertEqual(document_content.word_count, 2)
        self.assertEqual(document_content.char_count, 14)

    def test_extract_content_propagates_reference_extraction_port_error(self):
        document_text_port = FakeDocumentTextPort(paragraphs=["Paragraph text"])
        base_document_content = DocumentContentDTO(
            word_count=2, char_count=14, paragraphs=["Paragraph text"]
        )
        content_extraction_port = FakeContentExtractionPort(result=base_document_content)
        character_count_port = FakeCharacterCountPort(result=None)
        reference_extraction_port = FakeReferenceExtractionPort(
            error=RuntimeError("Reference extraction failed")
        )

        document_content_extractor = DocumentContentExtractor(
            document_text_port=document_text_port,
            content_extraction_port=content_extraction_port,
            character_count_port=character_count_port,
            reference_extraction_port=reference_extraction_port,
            article_body_locator=self._build_article_body_locator(),
            article_header_locator=self._build_article_header_locator(),
            document_table_port=FakeDocumentTablePort(),
            table_markdown_renderer=TableMarkdownRenderer(),
        )
        with self.assertRaises(RuntimeError):
            document_content_extractor.extract_content(docx_path="test.docx")

    def _build_article_body_locator(self) -> ArticleBodyLocator:
        editorial_norms = build_editorial_norms_for_test()
        return ArticleBodyLocator(
            abstract_norms=editorial_norms.abstract,
            keyword_norms=editorial_norms.keywords,
            bibliography_norms=editorial_norms.bibliography,
        )

    def _build_article_header_locator(self) -> ArticleHeaderLocator:
        return ArticleHeaderLocator(abstract_norms=build_editorial_norms_for_test().abstract)
