from pathlib import Path
from unittest import TestCase

from src.domain.dtos.bibliography_norms_dto import BibliographyNormsDTO
from src.domain.dtos.reference_dto import ReferenceDTO
from src.infrastructure.adapters.document.docx_reference_adapter import DocxReferenceAdapter
from src.infrastructure.adapters.document.docx_text_adapter import DocxTextAdapter

SAMPLE_DOCUMENT = (
    Path(__file__).parent.parent.parent.parent.parent.parent
    / "docs"
    / "sample-documents"
    / "1. test_Científico.docx"
)

_ALLOWED_SECTION_NAMES = {"Bibliografía", "Referencias", "Fuentes bibliográficas"}


class TestDocxReferenceAdapter(TestCase):
    def setUp(self):
        self.adapter = DocxReferenceAdapter(
            document_text_port=DocxTextAdapter(),
            bibliography_norms=BibliographyNormsDTO(
                header_markers=("referencias", "bibliografía"), header_max_length=30
            ),
        )
        self.references, self.section_type = self.adapter.extract_references(
            docx_path=str(SAMPLE_DOCUMENT)
        )

    def test_s8a_returns_non_empty_list_and_non_empty_string(self):
        self.assertIsInstance(self.references, list)
        self.assertGreater(len(self.references), 0)
        self.assertIsInstance(self.section_type, str)
        self.assertGreater(len(self.section_type), 0)

    def test_s8b_all_items_are_reference_dto(self):
        for item in self.references:
            self.assertIsInstance(item, ReferenceDTO)

    def test_s8c_section_type_is_valid_name(self):
        self.assertIn(self.section_type, _ALLOWED_SECTION_NAMES)
