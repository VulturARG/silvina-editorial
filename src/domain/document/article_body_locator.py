from src.domain.document.title_normalizer import TitleNormalizer
from src.domain.dtos.abstract_norms_dto import AbstractNormsDTO
from src.domain.dtos.article_body_dto import ArticleBodyDTO
from src.domain.dtos.bibliography_norms_dto import BibliographyNormsDTO
from src.domain.dtos.keyword_norms_dto import KeywordNormsDTO
from src.domain.exceptions.document_errors import DocumentBodyNotLocated, DocumentEmpty


class ArticleBodyLocator:
    """Domain service that locates the article title, abstract and body using editorial norms."""

    def __init__(
        self,
        abstract_norms: AbstractNormsDTO,
        keyword_norms: KeywordNormsDTO,
        bibliography_norms: BibliographyNormsDTO,
    ) -> None:
        self._abstract_norms = abstract_norms
        self._keyword_norms = keyword_norms
        self._bibliography_norms = bibliography_norms

    def locate(self, paragraphs: list[str]) -> ArticleBodyDTO:
        """Return the repeated title, the abstract paragraphs and the body paragraphs."""
        if not paragraphs:
            raise DocumentEmpty()
        title_index = self._find_repeated_title_index(paragraphs)
        header_index = self._find_bibliography_header_index(paragraphs, title_index)
        return ArticleBodyDTO(
            title=paragraphs[title_index],
            abstract_paragraphs=self._find_abstract_paragraphs(paragraphs, title_index),
            paragraphs=tuple(paragraphs[title_index + 1 : header_index]),
        )

    def _find_repeated_title_index(self, paragraphs: list[str]) -> int:
        search_key = TitleNormalizer.normalize(paragraphs[0])
        for index in range(1, len(paragraphs)):
            if TitleNormalizer.normalize(paragraphs[index]).startswith(search_key):
                return index
        raise DocumentBodyNotLocated()

    def _find_abstract_paragraphs(self, paragraphs: list[str], title_index: int) -> tuple[str, ...]:
        heading_index = self._find_abstract_heading_index(paragraphs, title_index)
        if heading_index is None:
            return ()
        end_index = self._find_keywords_index(paragraphs, heading_index + 1, title_index)
        return tuple(paragraphs[heading_index + 1 : end_index])

    def _find_abstract_heading_index(self, paragraphs: list[str], title_index: int) -> int | None:
        for index in range(title_index):
            if self._is_abstract_heading(paragraphs[index]):
                return index
        return None

    def _find_keywords_index(self, paragraphs: list[str], start_index: int, stop_index: int) -> int:
        for index in range(start_index, stop_index):
            if self._starts_with_any(paragraphs[index], self._keyword_norms.section_markers):
                return index
        return stop_index

    def _find_bibliography_header_index(self, paragraphs: list[str], title_index: int) -> int:
        for index in range(title_index + 1, len(paragraphs)):
            if self._is_bibliography_header(paragraphs[index]):
                return index
        return len(paragraphs)

    def _is_abstract_heading(self, paragraph: str) -> bool:
        heading = paragraph.lower().strip().rstrip(":").rstrip()
        return any(heading == keyword.lower() for keyword in self._abstract_norms.section_keywords)

    def _is_bibliography_header(self, paragraph: str) -> bool:
        lowered = paragraph.lower().strip()
        is_short = len(lowered) <= self._bibliography_norms.header_max_length
        return is_short and self._contains_any(lowered, self._bibliography_norms.header_markers)

    def _starts_with_any(self, paragraph: str, markers: tuple[str, ...]) -> bool:
        lowered = paragraph.lower()
        return any(lowered.startswith(marker.lower()) for marker in markers)

    def _contains_any(self, text: str, markers: tuple[str, ...]) -> bool:
        return any(marker.lower() in text for marker in markers)
