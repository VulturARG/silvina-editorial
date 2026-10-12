from unittest import TestCase

from src.domain.exceptions.base_src_error import BaseSrcError
from src.domain.exceptions.editorial_norms_errors import (
    EditorialNormInvalid,
    EditorialNormMissing,
    EditorialNormsError,
    EditorialNormsFileInvalid,
    EditorialNormsFileNotFound,
)


class TestEditorialNormsError(TestCase):
    def test_is_subclass_of_base_src_error(self):
        self.assertTrue(issubclass(EditorialNormsError, BaseSrcError))


class TestEditorialNormsFileNotFound(TestCase):
    def test_is_subclass_of_editorial_norms_error(self):
        self.assertTrue(issubclass(EditorialNormsFileNotFound, EditorialNormsError))

    def test_is_catchable_as_base_src_error(self):
        with self.assertRaises(BaseSrcError):
            raise EditorialNormsFileNotFound("editorial_norms.toml")

    def test_message_content(self):
        self.assertEqual(
            EditorialNormsFileNotFound.MESSAGE, "The editorial norms file could not be found."
        )

    def test_dict_contains_message_and_detail(self):
        self.assertEqual(
            EditorialNormsFileNotFound("editorial_norms.toml").dict(),
            {"error": "The editorial norms file could not be found. editorial_norms.toml"},
        )

    def test_exposes_the_detail(self):
        self.assertEqual(
            EditorialNormsFileNotFound("editorial_norms.toml").detail, "editorial_norms.toml"
        )


class TestEditorialNormsFileInvalid(TestCase):
    def test_is_subclass_of_editorial_norms_error(self):
        self.assertTrue(issubclass(EditorialNormsFileInvalid, EditorialNormsError))

    def test_is_catchable_as_base_src_error(self):
        with self.assertRaises(BaseSrcError):
            raise EditorialNormsFileInvalid("syntax error at line 3")

    def test_message_content(self):
        self.assertEqual(
            EditorialNormsFileInvalid.MESSAGE, "The editorial norms file is not valid TOML."
        )

    def test_dict_contains_message_and_detail(self):
        self.assertEqual(
            EditorialNormsFileInvalid("syntax error at line 3").dict(),
            {"error": "The editorial norms file is not valid TOML. syntax error at line 3"},
        )

    def test_exposes_the_detail(self):
        self.assertEqual(
            EditorialNormsFileInvalid("syntax error at line 3").detail, "syntax error at line 3"
        )


class TestEditorialNormMissing(TestCase):
    def test_is_subclass_of_editorial_norms_error(self):
        self.assertTrue(issubclass(EditorialNormMissing, EditorialNormsError))

    def test_is_catchable_as_base_src_error(self):
        with self.assertRaises(BaseSrcError):
            raise EditorialNormMissing("'margin_cm' in section [document_format]")

    def test_message_content(self):
        self.assertEqual(EditorialNormMissing.MESSAGE, "A required editorial norm is missing.")

    def test_dict_contains_message_and_detail(self):
        self.assertEqual(
            EditorialNormMissing("'margin_cm' in section [document_format]").dict(),
            {
                "error": "A required editorial norm is missing. 'margin_cm' in section [document_format]"
            },
        )

    def test_exposes_the_detail(self):
        self.assertEqual(
            EditorialNormMissing("'margin_cm' in section [document_format]").detail,
            "'margin_cm' in section [document_format]",
        )


class TestEditorialNormInvalid(TestCase):
    def test_is_subclass_of_editorial_norms_error(self):
        self.assertTrue(issubclass(EditorialNormInvalid, EditorialNormsError))

    def test_is_catchable_as_base_src_error(self):
        with self.assertRaises(BaseSrcError):
            raise EditorialNormInvalid("'margin_cm' in section [document_format] must be positive")

    def test_message_content(self):
        self.assertEqual(EditorialNormInvalid.MESSAGE, "An editorial norm has an invalid value.")

    def test_dict_contains_message_and_detail(self):
        self.assertEqual(
            EditorialNormInvalid(
                "'margin_cm' in section [document_format] must be positive"
            ).dict(),
            {
                "error": "An editorial norm has an invalid value. 'margin_cm' in section [document_format] must be positive"
            },
        )

    def test_exposes_the_detail(self):
        self.assertEqual(
            EditorialNormInvalid(
                "'margin_cm' in section [document_format] must be positive"
            ).detail,
            "'margin_cm' in section [document_format] must be positive",
        )
