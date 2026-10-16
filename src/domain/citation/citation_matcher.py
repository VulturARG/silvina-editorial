import re

from src.domain.dtos.citation_analysis_result_dto import CitationAnalysisResultDTO
from src.domain.dtos.citation_dto import CitationDTO
from src.domain.dtos.reference_dto import ReferenceDTO
from src.domain.enums.citation_type import CitationType
from src.domain.enums.section_name import SectionName


class CitationMatcher:
    """Matches in-text citations with reference list entries via normalized author keys."""

    _NON_AUTHOR_PATTERNS = [
        r"^[A-Z]{2,}\s+\d",
        r"^arXiv:",
        r"^doi:",
        r"^repositorio",
        r"^no hay",
        r"^\w.*\d{4}.*\d{4}",
    ]

    def _citable(self, citations: list[CitationDTO]) -> list[CitationDTO]:
        return [
            citation
            for citation in citations
            if citation.citation_type != CitationType.FOOTNOTE and citation.author
        ]

    def find_orphaned_citations(
        self, citations: list[CitationDTO], references: list[ReferenceDTO]
    ) -> list[CitationDTO]:
        """Return citations whose normalized author has no matching reference entry."""
        reference_keys = self._build_reference_keys(references)
        return [
            citation
            for citation in self._citable(citations)
            if self._is_orphaned_citation(citation, reference_keys)
        ]

    def find_orphaned_references(
        self, citations: list[CitationDTO], references: list[ReferenceDTO]
    ) -> list[ReferenceDTO]:
        """Return references never cited by any in-text citation."""
        citation_keys = self._build_citation_keys(citations)
        return [
            reference
            for reference in references
            if not any(key in citation_keys for key in self._reference_keys(reference))
        ]

    def match_citations_to_references(
        self,
        citations: list[CitationDTO],
        references: list[ReferenceDTO],
        section_type: SectionName = SectionName.REFERENCES,
    ) -> CitationAnalysisResultDTO:
        """Compute aggregate citation-reference match statistics for a section."""
        orphaned_citations = self.find_orphaned_citations(citations, references)
        valid_citations = self._citable(citations)
        return CitationAnalysisResultDTO(
            total_citations=len(valid_citations),
            total_references=len(references),
            matched_count=max(0, len(valid_citations) - len(orphaned_citations)),
            unmatched_count=len(orphaned_citations),
            citations_by_type={},
            unmatched_citations=[citation.text for citation in orphaned_citations],
        )

    def _build_citation_keys(self, citations: list[CitationDTO]) -> dict[str, CitationDTO]:
        return {
            self._normalize_author(citation.author): citation
            for citation in self._citable(citations)
        }

    def _build_reference_keys(self, references: list[ReferenceDTO]) -> dict[str, ReferenceDTO]:
        return {
            key: reference for reference in references for key in self._reference_keys(reference)
        }

    def _reference_keys(self, reference: ReferenceDTO) -> set[str]:
        """Return the surname key and, when the author part declares one, the acronym key."""
        keys = {self._normalize_author(reference.text)}
        acronym = self._normalize_acronym(reference.text)
        if acronym:
            keys.add(acronym)
        return keys

    def _is_orphaned_citation(
        self, citation: CitationDTO, reference_keys: dict[str, ReferenceDTO]
    ) -> bool:
        key = self._normalize_author(citation.author)
        return key != "__non_author__" and key not in reference_keys

    def _normalize_author(self, text: str) -> str:
        """Extract and normalize the first author surname; non-author text yields a sentinel."""
        text_stripped = text.strip().lstrip("(").rstrip(")")
        is_non_author = any(
            re.search(pattern, text_stripped, re.IGNORECASE)
            for pattern in self._NON_AUTHOR_PATTERNS
        )
        if is_non_author:
            return "__non_author__"

        text = self._author_part(text)
        text = re.sub(r"\s+et\s+al\.?.*", "", text, flags=re.IGNORECASE).strip()
        text = re.sub(r"\s+y\s+.*", "", text, flags=re.IGNORECASE).strip()
        text = re.sub(r"\b[A-ZÁÉÍÓÚÑ]\.\s*", "", text).strip()
        text = re.sub(r"[,&.()\[\]]", "", text).strip()

        words = text.split()
        return words[0].lower() if words else ""

    def _normalize_acronym(self, text: str) -> str:
        """Return the lowercased acronym declared in parentheses in the author part, or empty."""
        acronym_match = re.search(r"\(([A-ZÁÉÍÓÚÑÜ]{2,10})\)", self._author_part(text))
        return acronym_match.group(1).lower() if acronym_match else ""

    def _author_part(self, text: str) -> str:
        """Return the text preceding the parenthesized year, or the whole text if there is none."""
        year_match = re.search(r"\((?:\d{1,2}\s+de\s+\w+\s+de\s+)?\d{4}[a-z]?\)", text)
        return text[: year_match.start()].strip() if year_match else text
