from pathlib import Path
from unittest import TestCase

from src.domain.dtos.citation_dto import CitationDTO
from src.domain.enums.citation_type import CitationType
from src.infrastructure.adapters.document.docx_citation_adapter import DocxCitationAdapter
from src.infrastructure.adapters.document.docx_text_adapter import DocxTextAdapter

SAMPLE_DOCUMENT = (
    Path(__file__).parent.parent.parent.parent.parent.parent
    / "docs"
    / "sample-documents"
    / "1. test_Científico.docx"
)


class TestDocxCitationAdapter(TestCase):
    def setUp(self):
        self.adapter = DocxCitationAdapter(
            document_text_port=DocxTextAdapter(), max_author_name_length=100
        )
        self.result = self.adapter.extract_citations(docx_path=str(SAMPLE_DOCUMENT))

    def test_s7a_returns_non_empty_list(self):
        self.assertIsInstance(self.result, list)
        self.assertGreater(len(self.result), 0)

    def test_s7b_all_items_are_citation_dto(self):
        for item in self.result:
            self.assertIsInstance(item, CitationDTO)

    def test_s7c_citation_type_is_author_year(self):
        for item in self.result:
            self.assertEqual(item.citation_type, CitationType.AUTHOR_YEAR)

    def test_s7d_custom_max_author_name_length_rejects_long_author_name(self):
        adapter = DocxCitationAdapter(
            document_text_port=DocxTextAdapter(), max_author_name_length=5
        )
        full_text = "Como plantea Rodríguez y Fernández (2020), esto es relevante."
        citations = adapter._extract_citations(full_text=full_text)
        self.assertFalse(any(citation.author == "Rodríguez y Fernández" for citation in citations))

    def test_default_max_author_name_length_accepts_long_author_name(self):
        adapter = DocxCitationAdapter(
            document_text_port=DocxTextAdapter(), max_author_name_length=100
        )
        full_text = "Como plantea Rodríguez y Fernández (2020), esto es relevante."
        citations = adapter._extract_citations(full_text=full_text)
        self.assertTrue(any(citation.author == "Rodríguez y Fernández" for citation in citations))

    def test_s7e_citations_get_correct_paragraph_index(self):
        paragraphs = [
            "Este texto no tiene citas.",
            "Como plantea García (2019), esto es relevante.",
            "Otro párrafo sin citas.",
            "Martínez (2021) sostiene lo contrario.",
        ]
        citations = self.adapter._extract_citations(paragraphs=paragraphs)

        garcia = next(citation for citation in citations if citation.author == "García")
        martinez = next(citation for citation in citations if citation.author == "Martínez")
        self.assertEqual(garcia.location, 1)
        self.assertEqual(martinez.location, 3)

    def test_s7f_raw_text_fallback_assigns_location_zero(self):
        full_text = "Como plantea García (2019), esto es relevante."
        citations = self.adapter._extract_citations(full_text=full_text)
        self.assertTrue(citations)
        for citation in citations:
            self.assertEqual(citation.location, 0)

        citations_from_str = self.adapter._extract_citations(paragraphs=full_text)
        self.assertTrue(citations_from_str)
        for citation in citations_from_str:
            self.assertEqual(citation.location, 0)

    def test_parenthetical_group_with_semicolon_yields_one_citation_per_segment(self):
        full_text = "Estudios previos lo confirman (Dupuy et al., 2021; nota sin año; Boyes, 2015)."
        citations = self.adapter._extract_citations(full_text=full_text)
        self.assertEqual(
            [(citation.author, citation.year, citation.text) for citation in citations],
            [
                ("Dupuy et al.", "2021", "(Dupuy et al., 2021)"),
                ("Boyes", "2015", "(Boyes, 2015)"),
            ],
        )
