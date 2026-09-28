from unittest import TestCase

from src.domain.exceptions.base_src_error import BaseSrcError
from src.domain.exceptions.document_errors import DocumentError, DocumentInvalidType


class TestDocumentInvalidType(TestCase):
    def test_is_subclass_of_document_error(self):
        self.assertTrue(issubclass(DocumentInvalidType, DocumentError))

    def test_is_catchable_as_base_src_error(self):
        with self.assertRaises(BaseSrcError):
            raise DocumentInvalidType()

    def test_message_is_not_empty(self):
        self.assertGreater(len(DocumentInvalidType.MESSAGE), 0)

    def test_message_content(self):
        self.assertEqual(
            DocumentInvalidType.MESSAGE,
            "The document type is invalid. Only .docx files are supported.",
        )
