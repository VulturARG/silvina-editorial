from unittest import TestCase

from src.domain.exceptions.base_src_error import BaseSrcError
from src.domain.exceptions.document_errors import DocumentError, DocumentNotFound


class TestDocumentNotFound(TestCase):
    def test_is_subclass_of_document_error(self):
        self.assertTrue(issubclass(DocumentNotFound, DocumentError))

    def test_is_catchable_as_base_src_error(self):
        with self.assertRaises(BaseSrcError):
            raise DocumentNotFound()

    def test_message_is_not_empty(self):
        self.assertGreater(len(DocumentNotFound.MESSAGE), 0)

    def test_is_catchable_as_document_error_with_detail(self):
        with self.assertRaises(DocumentError):
            raise DocumentNotFound(detail="detail")

    def test_detail_is_none_when_not_given(self):
        self.assertIsNone(DocumentNotFound().detail)

    def test_dict_without_detail_contains_only_message(self):
        self.assertEqual(DocumentNotFound().dict(), {"error": DocumentNotFound.MESSAGE})

    def test_exposes_the_detail(self):
        self.assertEqual(DocumentNotFound(detail="detail").detail, "detail")

    def test_dict_contains_message_and_detail(self):
        self.assertEqual(
            DocumentNotFound(detail="detail").dict(),
            {"error": f"{DocumentNotFound.MESSAGE} detail"},
        )
