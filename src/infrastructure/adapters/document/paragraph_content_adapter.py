import re

from src.domain.document.content_extraction_port import ContentExtractionPort
from src.domain.dtos.document_content_dto import DocumentContentDTO
from src.domain.exceptions.document_errors import DocumentEmpty
from src.infrastructure.adapters.document.extraction_vocabulary import (
    SECTION_HEADERS,
    SECTION_PATTERNS,
)


class ParagraphContentAdapter(ContentExtractionPort):
    """Extracts structured content from raw document paragraphs."""

    def extract(self, paragraphs: list[str], docx_path: str | None = None) -> DocumentContentDTO:
        """Return a DocumentContentDTO with text-based counts and structured fields.

        Raises DocumentEmpty when all paragraphs are blank or the list is empty.
        The docx_path argument is accepted for interface compatibility but ignored —
        accurate COM-based counts are the responsibility of CharacterCountPort.
        """
        clean = [s for p in paragraphs if (s := str(p).strip())]
        if not clean:
            raise DocumentEmpty()
        return DocumentContentDTO(
            word_count=sum(len(p.split()) for p in clean),
            char_count=sum(len(p) for p in clean),
            paragraph_count=len(clean),
            keywords=self._extract_keywords(paragraphs=clean),
            references=[],
            paragraphs=clean,
            sections=self._extract_sections(paragraphs=clean),
        )

    def _extract_keywords(self, paragraphs: list[str]) -> list[str]:
        for para in paragraphs:
            if m := re.match(SECTION_PATTERNS["keywords"], para, re.IGNORECASE):
                return [kw.strip() for kw in re.split(r"[;,]", m.group(1).strip()) if kw.strip()]
        return []

    def _extract_sections(self, paragraphs: list[str]) -> dict[str, str]:
        sections: dict[str, str] = {}
        current_section: str | None = None
        current_content: list[str] = []
        for para in paragraphs:
            para_upper = para.strip().upper()
            if any(h in para_upper for h in SECTION_HEADERS) and len(para.split()) <= 5:
                if current_section and current_content:
                    sections[current_section] = "\n".join(current_content)
                current_section = para_upper
                current_content = []
                continue
            if current_section:
                current_content.append(para)
        if current_section and current_content:
            sections[current_section] = "\n".join(current_content)
        return sections
