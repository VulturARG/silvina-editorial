from inspect import getsource
from unittest import TestCase

from src.application.read_document_use_case import ReadDocumentUseCase
from src.infrastructure.adapters.document.docx_text_adapter import DocxTextAdapter
from src.infrastructure.wirings.read_document_use_case_wiring import ReadDocumentUseCaseWiring


class TestReadDocumentUseCaseWiring(TestCase):
    def test_create_use_case_returns_read_document_use_case_backed_by_docx_text_adapter(self):
        use_case = ReadDocumentUseCaseWiring().create_use_case()

        self.assertIsInstance(use_case, ReadDocumentUseCase)
        self.assertIsInstance(use_case._port, DocxTextAdapter)

    def test_docx_logic_confined_to_private_get_method(self):
        source = getsource(ReadDocumentUseCaseWiring.create_use_case)
        self.assertNotIn("docx", source)
        self.assertNotIn("Document(", source)
