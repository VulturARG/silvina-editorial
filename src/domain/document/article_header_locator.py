from src.domain.document.title_normalizer import TitleNormalizer
from src.domain.dtos.abstract_norms_dto import AbstractNormsDTO


class ArticleHeaderLocator:
    """Domain service that locates the author line printed right after the repeated article title."""

    MAXIMUM_TITLE_LINES = 3

    def __init__(self, abstract_norms: AbstractNormsDTO) -> None:
        self._abstract_norms = abstract_norms

    def locate_authors(self, paragraphs: list[str], repeated_title: str) -> str | None:
        """Return the paragraph after the title lines, or None when it is missing or an abstract heading."""
        title_line_count = self._find_title_line_count(
            paragraphs=paragraphs, repeated_title=repeated_title
        )
        if title_line_count is None or title_line_count >= len(paragraphs):
            return None
        candidate = paragraphs[title_line_count].strip()
        if self._is_abstract_heading(paragraph=candidate):
            return None
        return candidate

    def _find_title_line_count(self, paragraphs: list[str], repeated_title: str) -> int | None:
        normalized_title = TitleNormalizer.normalize(repeated_title)
        for line_count in range(1, min(self.MAXIMUM_TITLE_LINES, len(paragraphs)) + 1):
            if TitleNormalizer.normalize(" ".join(paragraphs[:line_count])) == normalized_title:
                return line_count
        return None

    def _is_abstract_heading(self, paragraph: str) -> bool:
        heading = paragraph.lower().strip().rstrip(":").rstrip()
        return any(heading == keyword.lower() for keyword in self._abstract_norms.section_keywords)
