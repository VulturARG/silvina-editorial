from inspect import getsource
from sys import modules
from unittest import TestCase

from src.domain.document.document_text_port import DocumentTextPort


class TestDocumentTextPort(TestCase):
    def test_is_abstract_base_class(self):
        with self.assertRaises(TypeError):
            DocumentTextPort()

    def test_declares_exactly_one_abstract_method_read_paragraphs(self):
        self.assertEqual(DocumentTextPort.__abstractmethods__, frozenset({"read_paragraphs"}))

    def test_module_has_no_docx_or_infrastructure_imports(self):
        module_source = getsource(modules[DocumentTextPort.__module__])
        self.assertNotIn("import docx", module_source)
        self.assertNotIn("src.infrastructure", module_source)
