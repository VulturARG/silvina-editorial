from unittest import TestCase

from src.domain.exceptions.base_src_error import BaseSrcError
from src.domain.exceptions.document_errors import DocumentBodyTooLong, DocumentError


class TestDocumentBodyTooLong(TestCase):
    def test_is_subclass_of_document_error(self):
        self.assertTrue(issubclass(DocumentBodyTooLong, DocumentError))

    def test_is_catchable_as_base_src_error(self):
        with self.assertRaises(BaseSrcError):
            raise DocumentBodyTooLong(body_characters=80000, maximum_body_characters=75000)

    def test_dict_contains_spanish_message_with_both_counts(self):
        error = DocumentBodyTooLong(body_characters=80000, maximum_body_characters=75000)

        self.assertEqual(
            error.dict(),
            {
                "error": (
                    "El cuerpo del artículo tiene 80000 caracteres y supera el máximo "
                    "permitido de 75000. No se realizó ningún análisis."
                )
            },
        )

    def test_exposes_body_characters_and_maximum(self):
        error = DocumentBodyTooLong(body_characters=80000, maximum_body_characters=75000)

        self.assertEqual(error.body_characters, 80000)
        self.assertEqual(error.maximum_body_characters, 75000)
