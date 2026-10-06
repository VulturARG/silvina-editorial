"""
Smoke test: DocumentContentExtractor fills references from real sample documents.

Exercises src.domain.document.document_content_extractor.DocumentContentExtractor
with the real text, content and reference adapters against the sample documents,
verifying the reference count and the S2a and S2b signals that the legacy
ContentExtractor produced for the same documents.

Run with: python -m pytest tests/smoke/ -v
"""

from pathlib import Path
from unittest import TestCase

from src.domain.classification.reference_signal_detector import ReferenceSignalDetector
from src.domain.document.document_content_extractor import DocumentContentExtractor
from src.domain.dtos.document_content_dto import DocumentContentDTO
from src.domain.tests.document.fake_character_count_port import FakeCharacterCountPort
from src.infrastructure.adapters.document.docx_reference_adapter import DocxReferenceAdapter
from src.infrastructure.adapters.document.docx_text_adapter import DocxTextAdapter
from src.infrastructure.adapters.document.paragraph_content_adapter import ParagraphContentAdapter

SAMPLE_DOCUMENTS_DIRECTORY = Path(__file__).parent.parent.parent / "docs" / "sample-documents"
SCIENTIFIC_DOCUMENT = "1. test_Científico.docx"
POPULAR_SCIENCE_DOCUMENT = "2. test_divulgacion_v2.docx"
OPINION_DOCUMENT = "3. test_opinion_v2.docx"


class TestExtractContentReferencesParity(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        document_text_adapter = DocxTextAdapter()
        cls.extractor = DocumentContentExtractor(
            document_text_port=document_text_adapter,
            content_extraction_port=ParagraphContentAdapter(),
            character_count_port=FakeCharacterCountPort(result=None),
            reference_extraction_port=DocxReferenceAdapter(
                document_text_port=document_text_adapter
            ),
        )
        cls.signal_detector = ReferenceSignalDetector()

    def _extract(self, document_name: str) -> DocumentContentDTO:
        return self.extractor.extract_content(
            docx_path=str(SAMPLE_DOCUMENTS_DIRECTORY / document_name)
        )

    def test_scientific_document_reaches_both_reference_signals(self) -> None:
        content = self._extract(SCIENTIFIC_DOCUMENT)

        self.assertEqual(len(content.references), 34)
        self.assertTrue(self.signal_detector.has_sufficient_count(content))
        self.assertTrue(self.signal_detector.has_recent_majority(content))

    def test_popular_science_document_reaches_neither_reference_signal(self) -> None:
        content = self._extract(POPULAR_SCIENCE_DOCUMENT)

        self.assertEqual(len(content.references), 11)
        self.assertFalse(self.signal_detector.has_sufficient_count(content))
        self.assertFalse(self.signal_detector.has_recent_majority(content))

    def test_opinion_document_reaches_neither_reference_signal(self) -> None:
        content = self._extract(OPINION_DOCUMENT)

        self.assertEqual(len(content.references), 4)
        self.assertFalse(self.signal_detector.has_sufficient_count(content))
        self.assertFalse(self.signal_detector.has_recent_majority(content))
