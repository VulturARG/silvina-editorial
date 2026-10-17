from unittest import TestCase

from src.domain.document.article_body_locator import ArticleBodyLocator
from src.domain.document.article_header_locator import ArticleHeaderLocator
from src.domain.document.document_content_extractor import DocumentContentExtractor
from src.domain.document.table_markdown_renderer import TableMarkdownRenderer
from src.domain.dtos.body_table_dto import BodyTableDTO
from src.domain.dtos.document_content_dto import DocumentContentDTO
from src.domain.dtos.document_table_dto import DocumentTableDTO
from src.domain.tests.document.fake_character_count_port import FakeCharacterCountPort
from src.domain.tests.document.fake_content_extraction_port import FakeContentExtractionPort
from src.domain.tests.document.fake_document_table_port import FakeDocumentTablePort
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
SCORE_TABLE_ROWS = (("Name", "Score"), ("Ana", "9"))
SCORE_TABLE_MARKDOWN = "| Name | Score |\n| --- | --- |\n| Ana | 9 |"


class TestDocumentContentExtractorTables(TestCase):
    def test_attaches_rendered_table_at_position_relative_to_body_paragraphs(self):
        extractor = self._build_extractor(
            document_table_port=FakeDocumentTablePort(
                tables=[DocumentTableDTO(rows=SCORE_TABLE_ROWS, position=5)]
            )
        )

        document_content = extractor.extract_content(docx_path="test.docx")

        self.assertEqual(
            document_content.body.tables,
            (BodyTableDTO(markdown=SCORE_TABLE_MARKDOWN, position=1),),
        )

    def test_reads_tables_of_the_docx_path_once(self):
        document_table_port = FakeDocumentTablePort(
            tables=[DocumentTableDTO(rows=SCORE_TABLE_ROWS, position=5)]
        )
        extractor = self._build_extractor(document_table_port=document_table_port)

        extractor.extract_content(docx_path="test.docx")

        self.assertEqual(document_table_port.read_paths, ["test.docx"])

    def test_skips_tables_whose_markdown_renders_empty(self):
        extractor = self._build_extractor(
            document_table_port=FakeDocumentTablePort(
                tables=[
                    DocumentTableDTO(rows=(), position=5),
                    DocumentTableDTO(rows=SCORE_TABLE_ROWS, position=5),
                ]
            )
        )

        document_content = extractor.extract_content(docx_path="test.docx")

        self.assertEqual(
            document_content.body.tables,
            (BodyTableDTO(markdown=SCORE_TABLE_MARKDOWN, position=1),),
        )

    def test_drops_tables_placed_outside_the_body(self):
        extractor = self._build_extractor(
            document_table_port=FakeDocumentTablePort(
                tables=[
                    DocumentTableDTO(rows=SCORE_TABLE_ROWS, position=0),
                    DocumentTableDTO(rows=SCORE_TABLE_ROWS, position=3),
                ]
            )
        )

        document_content = extractor.extract_content(docx_path="test.docx")

        self.assertEqual(document_content.body.tables, ())

    def test_tables_leave_body_text_and_paragraphs_unchanged(self):
        extractor = self._build_extractor(
            document_table_port=FakeDocumentTablePort(
                tables=[DocumentTableDTO(rows=SCORE_TABLE_ROWS, position=5)]
            )
        )

        document_content = extractor.extract_content(docx_path="test.docx")

        self.assertEqual(document_content.body.text, "Main title Body one. Body two.")
        self.assertEqual(document_content.paragraphs, ARTICLE_PARAGRAPHS)

    def _build_extractor(
        self, document_table_port: FakeDocumentTablePort
    ) -> DocumentContentExtractor:
        base_document_content = DocumentContentDTO(
            word_count=1, char_count=1, paragraphs=list(ARTICLE_PARAGRAPHS)
        )
        return DocumentContentExtractor(
            document_text_port=FakeDocumentTextPort(paragraphs=list(ARTICLE_PARAGRAPHS)),
            content_extraction_port=FakeContentExtractionPort(result=base_document_content),
            character_count_port=FakeCharacterCountPort(result=None),
            reference_extraction_port=FakeReferenceExtractionPort(result=([], "Referencias")),
            article_body_locator=self._build_article_body_locator(),
            article_header_locator=self._build_article_header_locator(),
            document_table_port=document_table_port,
            table_markdown_renderer=TableMarkdownRenderer(),
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
