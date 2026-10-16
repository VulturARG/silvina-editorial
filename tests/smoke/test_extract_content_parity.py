"""
Smoke test: ParagraphContentAdapter extracts structured content from real fixtures.

Exercises src.infrastructure.adapters.document.paragraph_content_adapter.
ParagraphContentAdapter directly against a real sample document, verifying
keywords and sections are extracted as expected.

Run with: python -m pytest tests/smoke/ -v
"""

from pathlib import Path
from unittest import TestCase

from src.infrastructure.adapters.document.docx_text_adapter import DocxTextAdapter
from src.infrastructure.adapters.document.paragraph_content_adapter import ParagraphContentAdapter

DOCS = Path(__file__).parent.parent.parent / "docs" / "sample-documents"
_DOCUMENT = "1. test_Científico.docx"


class TestExtractContentParity(TestCase):
    @classmethod
    def setUpClass(cls):
        paragraphs = DocxTextAdapter().read_paragraphs(path=str(DOCS / _DOCUMENT))
        cls.result = ParagraphContentAdapter().extract(paragraphs=paragraphs)

    def test_keywords_are_extracted(self):
        # These are the real values observed from ParagraphContentAdapter output for this fixture.
        self.assertEqual(
            self.result.keywords,
            [
                "modelos de lenguaje de gran escala",
                "capacidades emergentes",
                "aprendizaje en contexto",
                "razonamiento por cadena de pensamiento",
                "leyes de escala",
                "interpretabilidad mecanicista",
            ],
        )

    def test_sections_are_extracted(self):
        self.assertIn("REFERENCIAS", self.result.sections)
