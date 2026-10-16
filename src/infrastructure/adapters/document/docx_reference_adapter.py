from re import compile

from src.domain.document.document_text_port import DocumentTextPort
from src.domain.document.reference_extraction_port import ReferenceExtractionPort
from src.domain.dtos.bibliography_norms_dto import BibliographyNormsDTO
from src.domain.dtos.reference_dto import ReferenceDTO

_DEFAULT_SECTION_TYPE = "Referencias"

_SECTION_TYPE_MAP = {
    "ibliograf": "Bibliografía",
    "fuentes": "Fuentes bibliográficas",
}

_FIRST_YEAR_TOKEN_PATTERN = compile(
    r"\((?:\d{1,2}\s+de\s+\w+\s+de\s+)?\d{4}[a-z]?(?:,\s*\d{1,2}\s+de\s+\w+)?\)\.?"
)
_LEADING_BULLETS_PATTERN = compile(r"^[\•\-\*\·\s]+")


class DocxReferenceAdapter(ReferenceExtractionPort):
    """Extracts the references that follow the bibliography header, one reference per paragraph."""

    def __init__(
        self,
        document_text_port: DocumentTextPort,
        bibliography_norms: BibliographyNormsDTO,
    ) -> None:
        self._document_text_port = document_text_port
        self._bibliography_norms = bibliography_norms

    def extract_references(self, docx_path: str) -> tuple[list[ReferenceDTO], str]:
        """Return the references after the last bibliography header and the section type."""
        paragraphs = self._document_text_port.read_paragraphs(path=docx_path)
        header_index = self._find_bibliography_header_index(paragraphs=paragraphs)
        if header_index is None:
            return [], _DEFAULT_SECTION_TYPE
        section_type = self._resolve_section_type(label=paragraphs[header_index].lower())
        return self._build_references(paragraphs=paragraphs[header_index + 1 :]), section_type

    def _find_bibliography_header_index(self, paragraphs: list[str]) -> int | None:
        for index in reversed(range(len(paragraphs))):
            if self._is_bibliography_header(paragraph=paragraphs[index]):
                return index
        return None

    def _is_bibliography_header(self, paragraph: str) -> bool:
        lowered = paragraph.strip().lower()
        is_short = len(lowered) <= self._bibliography_norms.header_max_length
        return is_short and any(
            marker.lower() in lowered for marker in self._bibliography_norms.header_markers
        )

    def _resolve_section_type(self, label: str) -> str:
        for key, value in _SECTION_TYPE_MAP.items():
            if key in label:
                return value
        return _DEFAULT_SECTION_TYPE

    def _build_references(self, paragraphs: list[str]) -> list[ReferenceDTO]:
        references: list[ReferenceDTO] = []
        for paragraph in paragraphs:
            text = self._cut_after_first_year(text=self._strip_bullets(text=paragraph))
            if text:
                references.append(ReferenceDTO(text=text))
        return references

    def _strip_bullets(self, text: str) -> str:
        return _LEADING_BULLETS_PATTERN.sub("", text.strip()).strip()

    def _cut_after_first_year(self, text: str) -> str:
        match = _FIRST_YEAR_TOKEN_PATTERN.search(text)
        if match is None:
            return text
        return text[: match.end()]
