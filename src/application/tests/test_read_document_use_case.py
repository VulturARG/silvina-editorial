from inspect import getsource
from sys import modules
from unittest import TestCase

from src.application.read_document_use_case import ReadDocumentUseCase
from src.domain.exceptions.document_errors import DocumentNotFound
from src.domain.tests.document.fake_document_text_port import FakeDocumentTextPort


class TestReadDocumentUseCase(TestCase):
    def test_execute_returns_ports_result_unchanged(self):
        port = FakeDocumentTextPort(paragraphs=["A", "B"])
        use_case = ReadDocumentUseCase(port=port)

        result = use_case.execute("some/path.docx")

        self.assertEqual(result, ["A", "B"])

    def test_execute_propagates_document_not_found_unchanged(self):
        port = FakeDocumentTextPort(error=DocumentNotFound())
        use_case = ReadDocumentUseCase(port=port)

        with self.assertRaises(DocumentNotFound):
            use_case.execute("missing.docx")

    def test_module_does_not_import_document_content_dto(self):
        module_source = getsource(modules[ReadDocumentUseCase.__module__])
        self.assertNotIn("DocumentContentDTO", module_source)
