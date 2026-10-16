from re import compile, findall, split

from src.domain.document.citation_extraction_port import CitationExtractionPort
from src.domain.document.document_text_port import DocumentTextPort
from src.domain.dtos.citation_dto import CitationDTO
from src.domain.enums.citation_type import CitationType
from src.domain.exceptions.citation_errors import CitationParsingFailed  # noqa: F401

_INTRO_PHRASES = ("Como", "Según", "Si", "No", "En", "El", "La", "Los", "Las", "Un", "Una")

_PATTERN_PARENTHETICAL = compile(r"\([^)]*(?:19|20)\d{2}[^)]*\)")
_PATTERN_DATE_LIKE = compile(r"^\(\d+\s+de\s+")
_PATTERN_YEAR = compile(r"((?:19|20)\d{2})")
_PATTERN_MULTI_AUTHOR = compile(
    r"(?<![a-záéíóúñ])\b"
    r"([A-ZÁÉÍÓÚÑ][a-záéíóúñA-ZÁÉÍÓÚÑ]+"
    r"(?:\s+[ye&]\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñA-ZÁÉÍÓÚÑ\s]+?)+)"
    r"\s+\((\d{4}[a-z]?)\)"
)
_PATTERN_SINGLE_AUTHOR = compile(r"(?<![([])\b([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)\s+\((\d{4}[a-z]?)\)")


class DocxCitationAdapter(CitationExtractionPort):
    def __init__(
        self,
        document_text_port: DocumentTextPort,
        max_author_name_length: int,
    ) -> None:
        self._document_text_port = document_text_port
        self._max_author_name_length = max_author_name_length

    def extract_citations(self, docx_path: str) -> list[CitationDTO]:
        paragraphs = self._document_text_port.read_paragraphs(path=docx_path)
        return self._extract_citations(paragraphs=paragraphs)

    def _extract_citations(
        self,
        paragraphs: list[str] | str | None = None,
        full_text: str | None = None,
    ) -> list[CitationDTO]:
        if full_text is not None:
            paragraphs = [full_text]
        elif isinstance(paragraphs, str):
            paragraphs = [paragraphs]
        elif paragraphs is None:
            paragraphs = []

        citations: list[CitationDTO] = []
        seen: set[str] = set()
        multi_author_names: dict[str, set[str]] = {}
        first_authors_by_year: dict[str, set[str]] = {}
        for paragraph_index, paragraph_text in enumerate(paragraphs):
            self._collect_parenthetical(
                paragraph_text=paragraph_text,
                paragraph_index=paragraph_index,
                citations=citations,
                seen=seen,
                first_authors_by_year=first_authors_by_year,
            )
            self._collect_multi_author(
                paragraph_text=paragraph_text,
                paragraph_index=paragraph_index,
                citations=citations,
                seen=seen,
                multi_author_names=multi_author_names,
            )
            self._collect_single_author(
                paragraph_text=paragraph_text,
                paragraph_index=paragraph_index,
                citations=citations,
                seen=seen,
                first_authors_by_year=first_authors_by_year,
                multi_author_names=multi_author_names,
            )
        return citations

    def _collect_parenthetical(
        self,
        paragraph_text: str,
        paragraph_index: int,
        citations: list[CitationDTO],
        seen: set[str],
        first_authors_by_year: dict[str, set[str]],
    ) -> None:
        for match in _PATTERN_PARENTHETICAL.findall(paragraph_text):
            if _PATTERN_DATE_LIKE.match(match):
                continue
            for segment in match[1:-1].split(";"):
                self._collect_parenthetical_segment(
                    segment=segment,
                    paragraph_index=paragraph_index,
                    citations=citations,
                    seen=seen,
                    first_authors_by_year=first_authors_by_year,
                )

    def _collect_parenthetical_segment(
        self,
        segment: str,
        paragraph_index: int,
        citations: list[CitationDTO],
        seen: set[str],
        first_authors_by_year: dict[str, set[str]],
    ) -> None:
        year_match = _PATTERN_YEAR.search(segment)
        if not year_match:
            return
        year = year_match.group(1)
        author = segment[: year_match.start()].strip("(").strip().rstrip(",").strip()
        if len(author) < 2:
            return
        key = f"{author}|{year}"
        if key in seen:
            return
        seen.add(key)
        if "&" in author or "," in author:
            first = split(r"[,&]", author)[0].strip()
            first_authors_by_year.setdefault(year, set()).add(first)
        citations.append(
            CitationDTO(
                text=f"({segment.strip()})",
                citation_type=CitationType.AUTHOR_YEAR,
                location=paragraph_index,
                author=author,
                year=year,
            )
        )

    def _collect_multi_author(
        self,
        paragraph_text: str,
        paragraph_index: int,
        citations: list[CitationDTO],
        seen: set[str],
        multi_author_names: dict[str, set[str]],
    ) -> None:
        for author, year in _PATTERN_MULTI_AUTHOR.findall(paragraph_text):
            if len(author) > self._max_author_name_length or author.startswith(_INTRO_PHRASES):
                continue
            key = f"{author}|{year}"
            if key in seen:
                continue
            seen.add(key)
            multi_author_names.setdefault(year, set()).update(
                findall(r"[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+", author)
            )
            citations.append(
                CitationDTO(
                    text=f"{author} ({year})",
                    citation_type=CitationType.AUTHOR_YEAR,
                    location=paragraph_index,
                    author=author,
                    year=year,
                )
            )

    def _collect_single_author(
        self,
        paragraph_text: str,
        paragraph_index: int,
        citations: list[CitationDTO],
        seen: set[str],
        first_authors_by_year: dict[str, set[str]],
        multi_author_names: dict[str, set[str]],
    ) -> None:
        for author, year in _PATTERN_SINGLE_AUTHOR.findall(paragraph_text):
            if year in first_authors_by_year and author in first_authors_by_year[year]:
                continue
            if year in multi_author_names and author in multi_author_names[year]:
                continue
            key = f"{author}|{year}"
            if key in seen:
                continue
            seen.add(key)
            citations.append(
                CitationDTO(
                    text=f"{author} ({year})",
                    citation_type=CitationType.AUTHOR_YEAR,
                    location=paragraph_index,
                    author=author,
                    year=year,
                )
            )
