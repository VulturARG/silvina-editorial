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

    def test_is_catchable_as_document_error_with_detail(self):
        with self.assertRaises(DocumentError):
            raise DocumentInvalidType(detail="detail")

    def test_detail_is_none_when_not_given(self):
        self.assertIsNone(DocumentInvalidType().detail)

    def test_dict_without_detail_contains_only_message(self):
        self.assertEqual(DocumentInvalidType().dict(), {"error": DocumentInvalidType.MESSAGE})

    def test_exposes_the_detail(self):
        self.assertEqual(DocumentInvalidType(detail="detail").detail, "detail")

    def test_dict_contains_message_and_detail(self):
        self.assertEqual(
            DocumentInvalidType(detail="detail").dict(),
            {"error": f"{DocumentInvalidType.MESSAGE} detail"},
        )
