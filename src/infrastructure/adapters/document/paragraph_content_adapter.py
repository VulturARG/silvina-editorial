import re

from src.domain.document.content_extraction_port import ContentExtractionPort
from src.domain.dtos.document_content_dto import DocumentContentDTO
from src.domain.exceptions.document_errors import DocumentEmpty
from src.infrastructure.adapters.document.extraction_vocabulary import (
    AUTHOR_BLACKLIST,
    INSTITUTION_PATTERN,
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
        title = self._extract_title(paragraphs=clean)
        title_lines = (2 if title and " — " in title else 1) + bool(
            INSTITUTION_PATTERN.match(clean[0])
        )
        return DocumentContentDTO(
            word_count=sum(len(p.split()) for p in clean),
            char_count=sum(len(p) for p in clean),
            paragraph_count=len(clean),
            title=title,
            authors=self._extract_authors(paragraphs=clean, title_lines=title_lines),
            keywords=self._extract_keywords(paragraphs=clean),
            references=[],
            paragraphs=clean,
            sections=self._extract_sections(paragraphs=clean),
        )

    def _extract_title(self, paragraphs: list[str]) -> str | None:
        return self._try_explicit_title_marker(paragraphs=paragraphs) or self._try_inferred_title(
            paragraphs=paragraphs
        )

    def _try_explicit_title_marker(self, paragraphs: list[str]) -> str | None:
        for para in paragraphs[:5]:
            if m := re.match(SECTION_PATTERNS["title"], para, re.IGNORECASE):
                return m.group(1).strip()
        return None

    def _try_inferred_title(self, paragraphs: list[str]) -> str | None:
        candidates = self._collect_title_candidates(paragraphs=paragraphs)
        if not candidates:
            return None
        if len(candidates) == 1:
            return candidates[0]
        first, second = candidates[0], candidates[1]
        return first if self._looks_like_author(text=second) else f"{first.rstrip(':')} — {second}"

    def _collect_title_candidates(self, paragraphs: list[str]) -> list[str]:
        candidates: list[str] = []
        for para in paragraphs[:5]:
            if INSTITUTION_PATTERN.match(para):
                continue
            if len(para.split()) >= 2 and len(para) < 200:
                candidates.append(para.strip())
                if len(candidates) == 2:
                    break
        return candidates

    def _looks_like_author(self, text: str) -> bool:
        return (
            len(text.split()) <= 10
            and not any(c in text for c in ["—", "?", ":", "de", "del", "para"])
            and bool(
                text.count(";") >= 1
                or re.search(r"^(?:Dr|Dra|Lic|Mag|CF|CN|CNVGM|Prof)", text)
                or re.search(r"^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s*$", text)
                or re.search(r"^[A-Z]{2,}", text)
            )
        )

    def _extract_authors(self, paragraphs: list[str], title_lines: int = 1) -> str | None:
        for i, para in enumerate(paragraphs[title_lines:15], start=title_lines):
            if self._is_blacklisted(text=para):
                continue
            if result := (
                self._try_explicit_author_label(para=para, i=i, paragraphs=paragraphs)
                or self._try_parenthetical_author(para=para)
                or self._try_name_pattern(para=para, i=i, paragraphs=paragraphs)
            ):
                return result
        return None

    def _is_blacklisted(self, text: str) -> bool:
        return any(header in text.upper() for header in AUTHOR_BLACKLIST)

    def _try_explicit_author_label(self, para: str, i: int, paragraphs: list[str]) -> str | None:
        m = re.match(SECTION_PATTERNS["authors"], para, re.IGNORECASE)
        if not m:
            return None
        inline = m.group(1).strip()
        if inline and not self._is_blacklisted(text=inline):
            return inline
        lines: list[str] = []
        for next_para in paragraphs[i + 1 : i + 6]:
            stripped = next_para.strip()
            if not re.match(r"^[A-ZÁÉÍÓÚÑ]", stripped) or len(stripped.split()) > 10:
                break
            if self._is_blacklisted(text=stripped):
                break
            lines.append(stripped)
        return ", ".join(lines) if lines else None

    def _try_parenthetical_author(self, para: str) -> str | None:
        m = re.search(
            r"\((?:Director|Autor|Investigador|Coordinador).*?"
            r"([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3})\s*\)\d*",
            para,
            re.IGNORECASE,
        )
        return m.group(1).strip() if m else None

    def _try_name_pattern(self, para: str, i: int, paragraphs: list[str]) -> str | None:
        if i > 5:
            return None
        if len(para.split()) > 15 or not para[0].isupper() or para.isupper():
            return None
        if para.endswith(":") or not re.search(r"^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+", para):
            return None
        if self._is_blacklisted(text=para):
            return None
        author_text = para.strip()
        for next_para in paragraphs[i + 1 : i + 4]:
            stripped = next_para.strip()
            if not self._is_continuation_author(text=stripped):
                break
            author_text = author_text.rstrip(",;") + "; " + stripped.rstrip(",;")
        return author_text

    def _is_continuation_author(self, text: str) -> bool:
        return bool(
            text
            and len(text.split()) <= 15
            and text[0].isupper()
            and not text.isupper()
            and not text.endswith(":")
            and ";" in text
            and not self._is_blacklisted(text=text)
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
