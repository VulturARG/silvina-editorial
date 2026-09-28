from unittest import TestCase

from src.domain.exceptions.base_src_error import BaseSrcError
from src.domain.exceptions.document_errors import DocumentError, DocumentTooLarge


class TestDocumentTooLarge(TestCase):
    def test_is_subclass_of_document_error(self):
        self.assertTrue(issubclass(DocumentTooLarge, DocumentError))

    def test_is_catchable_as_base_src_error(self):
        with self.assertRaises(BaseSrcError):
            raise DocumentTooLarge()

    def test_message_is_not_empty(self):
        self.assertGreater(len(DocumentTooLarge.MESSAGE), 0)

    def test_message_content(self):
        self.assertEqual(
            DocumentTooLarge.MESSAGE,
            "The document file exceeds the maximum allowed size.",
        )
