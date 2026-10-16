from unittest import TestCase

from src.domain.document.article_body_locator import ArticleBodyLocator
from src.domain.document.article_header_locator import ArticleHeaderLocator
from src.domain.document.document_content_extractor import DocumentContentExtractor
from src.domain.dtos.article_body_dto import ArticleBodyDTO
from src.domain.dtos.document_content_dto import DocumentContentDTO
from src.domain.dtos.reference_dto import ReferenceDTO
from src.domain.exceptions.count_errors import CharacterCountUnavailable
from src.domain.exceptions.document_errors import DocumentBodyNotLocated
from src.domain.tests.document.fake_character_count_port import FakeCharacterCountPort
from src.domain.tests.document.fake_content_extraction_port import FakeContentExtractionPort
from src.domain.tests.document.fake_document_text_port import FakeDocumentTextPort
from src.domain.tests.document.fake_reference_extraction_port import FakeReferenceExtractionPort
from src.domain.tests.dtos.editorial_norms_builder_for_test import build_editorial_norms_for_test

ARTICLE_PARAGRAPHS = [
    "Main title",
    "Resumen",
    "Abstract sentence.",
    "Main title",
    "Body one.",
    "Body two.",
]


class TestDocumentContentExtractorBody(TestCase):
    """Unit tests for the body that DocumentContentExtractor attaches to the content."""

    def test_attaches_body_located_from_the_content_paragraphs(self):
        extractor = self._build_extractor(content_paragraphs=ARTICLE_PARAGRAPHS)

        document_content = extractor.extract_content(docx_path="test.docx")

        self.assertEqual(
            document_content.body,
            ArticleBodyDTO(
                title="Main title",
                abstract_paragraphs=("Abstract sentence.",),
                paragraphs=("Body one.", "Body two."),
            ),
        )

    def test_body_is_located_from_cleaned_content_paragraphs_not_from_raw_text(self):
        extractor = self._build_extractor(
            content_paragraphs=ARTICLE_PARAGRAPHS,
            raw_paragraphs=["Unlocatable raw text."],
        )

        document_content = extractor.extract_content(docx_path="test.docx")

        self.assertEqual(document_content.body.title, "Main title")
        self.assertEqual(document_content.body.paragraphs, ("Body one.", "Body two."))

    def test_sets_title_from_body_and_authors_from_the_paragraph_after_the_title(self):
        extractor = self._build_extractor(
            content_paragraphs=[
                "Main title",
                "Jane Doe",
                "Resumen",
                "Abstract sentence.",
                "Main title",
                "Body one.",
            ]
        )

        document_content = extractor.extract_content(docx_path="test.docx")

        self.assertEqual(document_content.title, "Main title")
        self.assertEqual(document_content.authors, "Jane Doe")

    def test_propagates_document_body_not_located_when_repeated_title_is_missing(self):
        extractor = self._build_extractor(content_paragraphs=["Main title", "Other paragraph."])

        with self.assertRaises(DocumentBodyNotLocated):
            extractor.extract_content(docx_path="test.docx")

    def test_body_location_leaves_paragraphs_counts_title_and_references_unchanged(self):
        base_document_content = DocumentContentDTO(
            word_count=7,
            char_count=40,
            paragraph_count=6,
            title="Main title",
            paragraphs=list(ARTICLE_PARAGRAPHS),
        )
        references = [ReferenceDTO(text="Reference one text")]
        extractor = self._build_extractor(
            content_paragraphs=ARTICLE_PARAGRAPHS,
            base_document_content=base_document_content,
            character_count_error=CharacterCountUnavailable(),
            references=references,
        )

        document_content = extractor.extract_content(docx_path="test.docx")

        self.assertEqual(document_content.paragraphs, ARTICLE_PARAGRAPHS)
        self.assertEqual(document_content.title, "Main title")
        self.assertEqual(document_content.word_count, 7)
        self.assertEqual(document_content.char_count, 40)
        self.assertEqual(document_content.paragraph_count, 6)
        self.assertEqual(document_content.references, references)

    def _build_extractor(
        self,
        content_paragraphs: list[str],
        raw_paragraphs: list[str] | None = None,
        base_document_content: DocumentContentDTO | None = None,
        character_count_error: Exception | None = None,
        references: list[ReferenceDTO] | None = None,
    ) -> DocumentContentExtractor:
        if base_document_content is None:
            base_document_content = DocumentContentDTO(
                word_count=1, char_count=1, paragraphs=content_paragraphs
            )
        if raw_paragraphs is None:
            raw_paragraphs = content_paragraphs
        return DocumentContentExtractor(
            document_text_port=FakeDocumentTextPort(paragraphs=raw_paragraphs),
            content_extraction_port=FakeContentExtractionPort(result=base_document_content),
            character_count_port=FakeCharacterCountPort(error=character_count_error),
            reference_extraction_port=FakeReferenceExtractionPort(
                result=(references or [], "Referencias")
            ),
            article_body_locator=self._build_article_body_locator(),
            article_header_locator=self._build_article_header_locator(),
        )

    def _build_article_body_locator(self) -> ArticleBodyLocator:
        editorial_norms = build_editorial_norms_for_test()
        return ArticleBodyLocator(
            abstract_norms=editorial_norms.abstract,
            keyword_norms=editorial_norms.keywords,
            bibliography_norms=editorial_norms.bibliography,
        )

    def _build_article_header_locator(self) -> ArticleHeaderLocator:
        return ArticleHeaderLocator(abstract_norms=build_editorial_norms_for_test().abstract)
