import re

from src.domain.dtos.apa_violation_dto import ApaViolationDTO
from src.domain.dtos.citation_dto import CitationDTO
from src.domain.dtos.reference_dto import ReferenceDTO
from src.domain.enums.apa_error_type import ApaErrorType
from src.domain.enums.citation_type import CitationType


class ApaValidator:
    """Validates APA 7 citation format for Spanish academic documents."""

    _NON_AUTHOR_PATTERNS = [
        r"^\([A-Z]{2,}\s+\d",
        r"^\(arXiv:",
        r"^\(doi:",
        r"^\(repositorio",
        r"^\(no hay",
        r"^\([a-záéíóúñ].*\d{4}.*\d{4}",
        r"^\(\w+\s+\w+.*\d{4}.*\d{4}",
    ]

    def validate_citation(
        self,
        citation_text: str,
        paragraph_index: int,
        paragraph_text: str = "",
        corporate_author_names: frozenset[str] = frozenset(),
    ) -> list[ApaViolationDTO]:
        """Validate a single citation and return all APA violations found."""
        is_parenthetical = citation_text.startswith("(") and citation_text.endswith(")")
        preview = paragraph_text[:30] + "..." if len(paragraph_text) > 30 else paragraph_text
        if is_parenthetical:
            return self._validate_parenthetical(
                citation_text, paragraph_index, preview, corporate_author_names
            )
        return self._validate_narrative(
            citation_text, paragraph_index, preview, corporate_author_names
        )

    def validate_all_citations(
        self,
        citations: list[CitationDTO],
        paragraphs: list[str],
        references: list[ReferenceDTO] | None = None,
    ) -> list[ApaViolationDTO]:
        """Filter AUTHOR_YEAR citations and validate each against its paragraph text."""
        corporate_author_names = self._build_corporate_author_names(references or [])
        all_violations = []
        for citation in citations:
            if citation.citation_type != CitationType.AUTHOR_YEAR:
                continue
            paragraph_text = (
                paragraphs[citation.location] if 0 <= citation.location < len(paragraphs) else ""
            )
            all_violations.extend(
                self.validate_citation(
                    citation.text, citation.location, paragraph_text, corporate_author_names
                )
            )
        return all_violations

    def _build_corporate_author_names(self, references: list[ReferenceDTO]) -> frozenset[str]:
        author_parts = [self._reference_author_part(reference.text) for reference in references]
        return frozenset(
            self._normalize_author_name(author_part)
            for author_part in author_parts
            if " & " in author_part and "," not in author_part
        )

    def _reference_author_part(self, reference_text: str) -> str:
        return reference_text.split("(", 1)[0].strip().removesuffix(".").strip()

    def _parenthetical_author_part(self, inner: str) -> str:
        return re.split(r",?\s*\d{4}[a-z]?", inner, maxsplit=1)[0].strip()

    def _is_corporate_author(
        self, author_part: str, corporate_author_names: frozenset[str]
    ) -> bool:
        return self._normalize_author_name(author_part) in corporate_author_names

    def _normalize_author_name(self, author_part: str) -> str:
        return " ".join(author_part.lower().split())

    def _validate_parenthetical(
        self,
        citation: str,
        location: int,
        preview: str = "",
        corporate_author_names: frozenset[str] = frozenset(),
    ) -> list[ApaViolationDTO]:
        inner = citation[1:-1].strip()
        author_part = self._parenthetical_author_part(inner)

        pre_skip = (
            []
            if self._is_corporate_author(author_part, corporate_author_names)
            else [self._check_conjunction(citation, inner, location, preview)]
        )

        if self._is_non_author_citation(citation):
            return [v for v in pre_skip if v]

        post_skip = [
            check(citation, inner, location, preview)
            for check in [
                self._check_comma,
                self._check_capitalization,
                self._check_et_al_format,
                self._check_page_format,
                self._check_spacing,
            ]
        ]
        return [v for v in pre_skip + post_skip if v]

    def _validate_narrative(
        self,
        citation: str,
        location: int,
        preview: str = "",
        corporate_author_names: frozenset[str] = frozenset(),
    ) -> list[ApaViolationDTO]:
        pattern = r"([A-ZÁÉÍÓÚÑ][a-záéíóúñA-ZÁÉÍÓÚÑ\-\s&.]+?)[\s]*\((\d{4}[a-z]?)\)"
        match = re.match(pattern, citation)
        if not match:
            return []
        author_part = match.group(1).strip()
        conjunction_violations = (
            []
            if self._is_corporate_author(author_part, corporate_author_names)
            else [self._check_narrative_conjunction(citation, author_part, location, preview)]
        )
        other_violations = [
            self._check_narrative_et_al(citation, author_part, location, preview),
            self._check_narrative_spacing(citation, author_part, location, preview),
        ]
        return [v for v in conjunction_violations + other_violations if v]

    def _check_conjunction(
        self, citation: str, inner: str, location: int, preview: str
    ) -> ApaViolationDTO | None:
        if " & " not in inner:
            return None
        return ApaViolationDTO(
            citation_text=citation,
            error_type=ApaErrorType.CONJUNCTION_ERROR,
            location=location,
            explanation='APA 7 español requiere "y" en lugar de "&" para citas parentéticas',
            correction=citation.replace(" & ", " y "),
            paragraph_preview=preview,
        )

    def _is_non_author_citation(self, citation: str) -> bool:
        return any(
            re.search(pattern, citation, re.IGNORECASE) for pattern in self._NON_AUTHOR_PATTERNS
        )

    def _check_comma(
        self, citation: str, inner: str, location: int, preview: str
    ) -> ApaViolationDTO | None:
        pattern_no_comma = r"\(([A-ZÁÉÍÓÚÑ][a-záéíóúñA-ZÁÉÍÓÚÑ\-]+)\s+(\d{4}[a-z]?)\)"
        match = re.match(pattern_no_comma, citation)
        if not (match and "," not in citation):
            return None
        return ApaViolationDTO(
            citation_text=citation,
            error_type=ApaErrorType.COMMA_ERROR,
            location=location,
            explanation="Falta coma entre autor y año",
            correction=f"({match.group(1)}, {match.group(2)})",
            paragraph_preview=preview,
        )

    def _check_capitalization(
        self, citation: str, inner: str, location: int, preview: str
    ) -> ApaViolationDTO | None:
        if not re.search(r"\(([a-záéíóúñ][a-záéíóúñA-ZÁÉÍÓÚÑ\-]+)", citation):
            return None
        return ApaViolationDTO(
            citation_text=citation,
            error_type=ApaErrorType.CAPITALIZATION_ERROR,
            location=location,
            explanation="El apellido debe comenzar con mayúscula",
            correction=citation.capitalize(),
            paragraph_preview=preview,
        )

    def _check_et_al_format(
        self, citation: str, inner: str, location: int, preview: str
    ) -> ApaViolationDTO | None:
        if not re.search(r"\bet\.?\s+al\b", inner, re.IGNORECASE):
            return None
        if "et. al" in inner:
            return ApaViolationDTO(
                citation_text=citation,
                error_type=ApaErrorType.ET_AL_FORMAT_ERROR,
                location=location,
                explanation='Formato incorrecto: debe ser "et al." (sin punto en "et")',
                correction=re.sub(r"et\.\s+al", "et al", citation, flags=re.IGNORECASE),
                paragraph_preview=preview,
            )
        if re.search(r"et al[,\)]", inner):
            return ApaViolationDTO(
                citation_text=citation,
                error_type=ApaErrorType.ET_AL_FORMAT_ERROR,
                location=location,
                explanation='Falta punto después de "al": debe ser "et al."',
                correction=re.sub(r"et al\b(?!\.)", "et al.", citation, flags=re.IGNORECASE),
                paragraph_preview=preview,
            )
        return None

    def _check_page_format(
        self, citation: str, inner: str, location: int, preview: str
    ) -> ApaViolationDTO | None:
        if "pág" not in inner.lower() and "página" not in inner.lower():
            return None
        return ApaViolationDTO(
            citation_text=citation,
            error_type=ApaErrorType.PAGE_FORMAT_ERROR,
            location=location,
            explanation='Usar abreviatura en inglés: "p." para página única, "pp." para múltiples',
            correction=citation.replace("pág.", "p.").replace("págs.", "pp."),
            paragraph_preview=preview,
        )

    def _check_spacing(
        self, citation: str, inner: str, location: int, preview: str
    ) -> ApaViolationDTO | None:
        if "  " not in citation:
            return None
        return ApaViolationDTO(
            citation_text=citation,
            error_type=ApaErrorType.SPACING_ERROR,
            location=location,
            explanation="Espaciado excesivo detectado",
            correction=" ".join(citation.split()),
            paragraph_preview=preview,
        )

    def _check_narrative_conjunction(
        self, citation: str, author_part: str, location: int, preview: str
    ) -> ApaViolationDTO | None:
        if " & " not in author_part:
            return None
        return ApaViolationDTO(
            citation_text=citation,
            error_type=ApaErrorType.CONJUNCTION_ERROR,
            location=location,
            explanation='APA 7 español requiere "y" en lugar de "&" para citas narrativas',
            correction=citation.replace(" & ", " y "),
            paragraph_preview=preview,
        )

    def _check_narrative_et_al(
        self, citation: str, author_part: str, location: int, preview: str
    ) -> ApaViolationDTO | None:
        if "et. al" not in author_part:
            return None
        return ApaViolationDTO(
            citation_text=citation,
            error_type=ApaErrorType.ET_AL_FORMAT_ERROR,
            location=location,
            explanation='Formato incorrecto: debe ser "et al." (sin punto en "et")',
            correction=citation.replace("et. al", "et al"),
            paragraph_preview=preview,
        )

    def _check_narrative_spacing(
        self, citation: str, author_part: str, location: int, preview: str
    ) -> ApaViolationDTO | None:
        if re.search(r"\s\(\d{4}[a-z]?\)", citation):
            return None
        return ApaViolationDTO(
            citation_text=citation,
            error_type=ApaErrorType.SPACING_ERROR,
            location=location,
            explanation="Debe haber un espacio entre el autor y el año",
            correction=re.sub(r"([A-Za-z])\(", r"\1 (", citation),
            paragraph_preview=preview,
        )
