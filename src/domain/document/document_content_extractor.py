from dataclasses import replace

from src.domain.document.article_body_locator import ArticleBodyLocator
from src.domain.document.article_header_locator import ArticleHeaderLocator
from src.domain.document.character_count_port import CharacterCountPort
from src.domain.document.content_extraction_port import ContentExtractionPort
from src.domain.document.document_text_port import DocumentTextPort
from src.domain.document.reference_extraction_port import ReferenceExtractionPort
from src.domain.dtos.document_content_dto import DocumentContentDTO
from src.domain.exceptions.count_errors import CharacterCountUnavailable


class DocumentContentExtractor:
    """Domain service that extracts document content, applying count fallback logic."""

    def __init__(
        self,
        document_text_port: DocumentTextPort,
        content_extraction_port: ContentExtractionPort,
        character_count_port: CharacterCountPort,
        reference_extraction_port: ReferenceExtractionPort,
        article_body_locator: ArticleBodyLocator,
        article_header_locator: ArticleHeaderLocator,
    ) -> None:
        self._document_text_port = document_text_port
        self._content_extraction_port = content_extraction_port
        self._character_count_port = character_count_port
        self._reference_extraction_port = reference_extraction_port
        self._article_body_locator = article_body_locator
        self._article_header_locator = article_header_locator

    def extract_content(self, docx_path: str) -> DocumentContentDTO:
        """Extract document content, replacing counts with accurate values when available."""
        paragraphs = self._document_text_port.read_paragraphs(path=docx_path)
        base = self._content_extraction_port.extract(paragraphs=paragraphs, docx_path=docx_path)
        references, _ = self._reference_extraction_port.extract_references(docx_path=docx_path)
        body = self._article_body_locator.locate(paragraphs=base.paragraphs)
        base = replace(
            base,
            title=body.title,
            authors=self._article_header_locator.locate_authors(
                paragraphs=base.paragraphs, repeated_title=body.title
            ),
            references=references,
            body=body,
        )
        try:
            counts = self._character_count_port.count(docx_path=docx_path)
        except CharacterCountUnavailable:
            return base
        if counts is None:
            return base
        return replace(
            base,
            word_count=counts.word_count,
            char_count=counts.char_count,
            paragraph_count=counts.paragraph_count,
        )
