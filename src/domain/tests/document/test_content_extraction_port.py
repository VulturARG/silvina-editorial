from inspect import getsource, signature
from sys import modules
from unittest import TestCase

from src.domain.document.content_extraction_port import ContentExtractionPort


class TestContentExtractionPort(TestCase):
    def test_is_abstract_base_class(self):
        with self.assertRaises(TypeError):
            ContentExtractionPort()

    def test_declares_exactly_one_abstract_method_extract(self):
        self.assertEqual(ContentExtractionPort.__abstractmethods__, frozenset({"extract"}))

    def test_extract_signature_has_paragraphs_and_optional_docx_path(self):
        sig = signature(ContentExtractionPort.extract)
        parameters = list(sig.parameters.keys())
        self.assertIn("paragraphs", parameters)
        self.assertIn("docx_path", parameters)
        self.assertIsNone(sig.parameters["docx_path"].default)

    def test_module_has_no_infrastructure_imports(self):
        module_source = getsource(modules[ContentExtractionPort.__module__])
        self.assertNotIn("src.infrastructure", module_source)
        self.assertNotIn("import docx", module_source)
        self.assertNotIn("import win32com", module_source)
