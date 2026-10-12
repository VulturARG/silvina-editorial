from unittest import TestCase

from src.domain.exceptions.editorial_norms_errors import (
    EditorialNormInvalid,
    EditorialNormMissing,
)
from src.infrastructure.editorial_norms_value_resolver import (
    EditorialNormsValueResolver,
)


class TestEditorialNormsValueResolver(TestCase):
    def setUp(self):
        norms = {
            "document_format": {
                "margin_cm": 2.5,
                "font_size_pt": 12,
                "allowed_fonts": ["Times New Roman", "Arial"],
                "flag": True,
                "text_as_number": "12",
                "empty_list": [],
                "blank_item_list": ["Times New Roman", "   "],
                "non_string_item_list": ["Times New Roman", 123],
                "not_a_list": "Arial",
            },
            "aliases_table": {
                "Summary": ["resumen", "abstract"],
                "Introduction": ["introducción", "introduction"],
            },
            "table_with_empty_list": {
                "Summary": [],
            },
            "table_with_blank_string": {
                "Summary": ["resumen", "   "],
            },
            "table_with_non_string": {
                "Summary": ["resumen", 123],
            },
            "table_with_not_a_list": {
                "Summary": "resumen",
            },
            "not_a_table": "just a string",
        }
        self._resolver = EditorialNormsValueResolver(norms)

    def test_reads_integer(self):
        value = self._resolver.read_integer("document_format", "font_size_pt")

        self.assertEqual(value, 12)
        self.assertIsInstance(value, int)

    def test_raises_editorial_norm_invalid_when_integer_is_not_an_integer(self):
        with self.assertRaises(EditorialNormInvalid) as context:
            self._resolver.read_integer("document_format", "margin_cm")
        self.assertRegex(context.exception.dict()["error"], r"'margin_cm'.*\[document_format\]")

    def test_raises_editorial_norm_invalid_when_integer_is_a_boolean(self):
        with self.assertRaises(EditorialNormInvalid) as context:
            self._resolver.read_integer("document_format", "flag")
        self.assertRegex(context.exception.dict()["error"], r"'flag'.*\[document_format\]")

    def test_raises_editorial_norm_invalid_when_integer_is_text(self):
        with self.assertRaises(EditorialNormInvalid) as context:
            self._resolver.read_integer("document_format", "text_as_number")
        self.assertRegex(
            context.exception.dict()["error"], r"'text_as_number'.*\[document_format\]"
        )

    def test_reads_float(self):
        value = self._resolver.read_float("document_format", "margin_cm")

        self.assertAlmostEqual(value, 2.5)

    def test_reads_integer_as_float(self):
        value = self._resolver.read_float("document_format", "font_size_pt")

        self.assertEqual(value, 12.0)
        self.assertIsInstance(value, float)

    def test_raises_editorial_norm_invalid_when_float_is_a_boolean(self):
        with self.assertRaises(EditorialNormInvalid) as context:
            self._resolver.read_float("document_format", "flag")
        self.assertRegex(context.exception.dict()["error"], r"'flag'.*\[document_format\]")

    def test_raises_editorial_norm_invalid_when_float_is_not_a_number(self):
        with self.assertRaises(EditorialNormInvalid) as context:
            self._resolver.read_float("document_format", "text_as_number")
        self.assertRegex(
            context.exception.dict()["error"], r"'text_as_number'.*\[document_format\]"
        )

    def test_reads_string_list_as_tuple(self):
        value = self._resolver.read_string_list("document_format", "allowed_fonts")

        self.assertEqual(value, ("Times New Roman", "Arial"))
        self.assertIsInstance(value, tuple)

    def test_raises_editorial_norm_invalid_when_string_list_is_not_a_list(self):
        with self.assertRaises(EditorialNormInvalid) as context:
            self._resolver.read_string_list("document_format", "not_a_list")
        self.assertRegex(context.exception.dict()["error"], r"'not_a_list'.*\[document_format\]")

    def test_raises_editorial_norm_invalid_when_string_list_is_empty(self):
        with self.assertRaises(EditorialNormInvalid) as context:
            self._resolver.read_string_list("document_format", "empty_list")
        self.assertRegex(context.exception.dict()["error"], r"'empty_list'.*\[document_format\]")

    def test_raises_editorial_norm_invalid_when_string_list_contains_blank_string(self):
        with self.assertRaises(EditorialNormInvalid) as context:
            self._resolver.read_string_list("document_format", "blank_item_list")
        self.assertRegex(
            context.exception.dict()["error"], r"'blank_item_list'.*\[document_format\]"
        )

    def test_raises_editorial_norm_invalid_when_string_list_contains_non_string_element(self):
        with self.assertRaises(EditorialNormInvalid) as context:
            self._resolver.read_string_list("document_format", "non_string_item_list")
        self.assertRegex(
            context.exception.dict()["error"], r"'non_string_item_list'.*\[document_format\]"
        )

    def test_raises_editorial_norm_missing_when_key_is_missing(self):
        with self.assertRaises(EditorialNormMissing) as context:
            self._resolver.read_integer("document_format", "missing_key")
        self.assertRegex(context.exception.dict()["error"], r"'missing_key'.*\[document_format\]")

    def test_raises_editorial_norm_missing_when_section_is_missing(self):
        with self.assertRaises(EditorialNormMissing) as context:
            self._resolver.read_integer("missing_section", "missing_key")
        self.assertRegex(context.exception.dict()["error"], r"'missing_key'.*\[missing_section\]")

    def test_reads_string_list_table(self):
        value = self._resolver.read_string_list_table("aliases_table")

        self.assertEqual(
            value,
            {
                "Summary": ("resumen", "abstract"),
                "Introduction": ("introducción", "introduction"),
            },
        )
        self.assertEqual(list(value.keys()), ["Summary", "Introduction"])

    def test_raises_editorial_norm_missing_when_string_list_table_section_is_missing(self):
        with self.assertRaises(EditorialNormMissing) as context:
            self._resolver.read_string_list_table("missing_section")
        self.assertRegex(context.exception.dict()["error"], r"\[missing_section\]")

    def test_raises_editorial_norm_invalid_when_string_list_table_is_not_a_dict(self):
        with self.assertRaises(EditorialNormInvalid) as context:
            self._resolver.read_string_list_table("not_a_table")
        self.assertRegex(context.exception.dict()["error"], r"\[not_a_table\]")

    def test_raises_editorial_norm_invalid_when_string_list_table_value_is_not_a_list(self):
        with self.assertRaises(EditorialNormInvalid) as context:
            self._resolver.read_string_list_table("table_with_not_a_list")
        self.assertRegex(context.exception.dict()["error"], r"'Summary'.*\[table_with_not_a_list\]")

    def test_raises_editorial_norm_invalid_when_string_list_table_value_is_empty(self):
        with self.assertRaises(EditorialNormInvalid) as context:
            self._resolver.read_string_list_table("table_with_empty_list")
        self.assertRegex(context.exception.dict()["error"], r"'Summary'.*\[table_with_empty_list\]")

    def test_raises_editorial_norm_invalid_when_string_list_table_contains_blank_string(self):
        with self.assertRaises(EditorialNormInvalid) as context:
            self._resolver.read_string_list_table("table_with_blank_string")
        self.assertRegex(
            context.exception.dict()["error"], r"'Summary'.*\[table_with_blank_string\]"
        )

    def test_raises_editorial_norm_invalid_when_string_list_table_contains_non_string_element(self):
        with self.assertRaises(EditorialNormInvalid) as context:
            self._resolver.read_string_list_table("table_with_non_string")
        self.assertRegex(context.exception.dict()["error"], r"'Summary'.*\[table_with_non_string\]")
