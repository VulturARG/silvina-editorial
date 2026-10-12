from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from src.domain.dtos.editorial_norms_dto import EditorialNormsDTO
from src.domain.exceptions.editorial_norms_errors import EditorialNormInvalid
from src.infrastructure.editorial_norms_loader import EditorialNormsLoader

PROJECT_EDITORIAL_NORMS_PATH = Path(__file__).resolve().parents[3] / "editorial_norms.toml"


class TestEditorialNormsLoader(TestCase):
    def setUp(self):
        self._temporary_directory = TemporaryDirectory()
        self.addCleanup(self._temporary_directory.cleanup)
        self._editorial_norms_file_path = (
            Path(self._temporary_directory.name) / "editorial_norms.toml"
        )

    def _write_valid_norms_file(self) -> None:
        content = (
            "[document_format]\n"
            "margin_cm = 2.5\n"
            "margin_tolerance_cm = 0.3\n"
            "font_size_pt = 12\n"
            "font_size_tolerance_pt = 1.0\n"
            'allowed_fonts = ["Times New Roman", "Arial", "Calibri"]\n'
            "max_unjustified_paragraph_ratio = 0.3\n"
            "\n"
            "[figures]\n"
            'caption_prefixes = ["figura", "fig.", "figure"]\n'
            "\n"
            "[tables]\n"
            'caption_prefixes = ["tabla", "table", "cuadro"]\n'
            "\n"
            "[abstract]\n"
            'section_keywords = ["resumen", "abstract", "síntesis", "sumario"]\n'
            "min_word_count = 100\n"
            "max_word_count = 300\n"
            "\n"
            "[keywords]\n"
            'section_markers = ["palabras clave", "keywords", "key words", "descriptores"]\n'
            "min_count = 3\n"
            "max_count = 5\n"
        )
        self._editorial_norms_file_path.write_text(content, encoding="utf-8")

    def _write_norms_with_replacement(self, original_line: str, replacement_line: str) -> None:
        self._write_valid_norms_file()
        current_content = self._editorial_norms_file_path.read_text(encoding="utf-8")
        self.assertIn(original_line, current_content)
        self._editorial_norms_file_path.write_text(
            current_content.replace(original_line, replacement_line), encoding="utf-8"
        )

    def test_loads_complete_editorial_norms_dto(self):
        self._write_valid_norms_file()

        norms = EditorialNormsLoader(self._editorial_norms_file_path).load()

        self.assertIsInstance(norms, EditorialNormsDTO)
        self.assertEqual(norms.document_format.margin_cm, 2.5)
        self.assertEqual(norms.document_format.margin_tolerance_cm, 0.3)
        self.assertEqual(norms.document_format.font_size_pt, 12.0)
        self.assertEqual(norms.document_format.font_size_tolerance_pt, 1.0)
        self.assertEqual(
            norms.document_format.allowed_fonts, ("Times New Roman", "Arial", "Calibri")
        )
        self.assertEqual(norms.document_format.max_unjustified_paragraph_ratio, 0.3)
        self.assertEqual(norms.figure_captions.caption_prefixes, ("figura", "fig.", "figure"))
        self.assertEqual(norms.table_captions.caption_prefixes, ("tabla", "table", "cuadro"))
        self.assertEqual(
            norms.abstract.section_keywords, ("resumen", "abstract", "síntesis", "sumario")
        )
        self.assertEqual(norms.abstract.min_word_count, 100)
        self.assertEqual(norms.abstract.max_word_count, 300)
        self.assertEqual(
            norms.keywords.section_markers,
            ("palabras clave", "keywords", "key words", "descriptores"),
        )
        self.assertEqual(norms.keywords.min_count, 3)
        self.assertEqual(norms.keywords.max_count, 5)

    def test_raises_editorial_norm_invalid_when_margin_cm_is_zero_or_negative(self):
        self._write_norms_with_replacement("margin_cm = 2.5", "margin_cm = 0.0")

        with self.assertRaises(EditorialNormInvalid) as context:
            EditorialNormsLoader(self._editorial_norms_file_path).load()

        self.assertRegex(context.exception.dict()["error"], r"'margin_cm'.*\[document_format\]")

    def test_raises_editorial_norm_invalid_when_margin_tolerance_cm_is_negative(self):
        self._write_norms_with_replacement(
            "margin_tolerance_cm = 0.3", "margin_tolerance_cm = -0.1"
        )

        with self.assertRaises(EditorialNormInvalid) as context:
            EditorialNormsLoader(self._editorial_norms_file_path).load()

        self.assertRegex(
            context.exception.dict()["error"], r"'margin_tolerance_cm'.*\[document_format\]"
        )

    def test_raises_editorial_norm_invalid_when_font_size_pt_is_zero_or_negative(self):
        self._write_norms_with_replacement("font_size_pt = 12", "font_size_pt = 0")

        with self.assertRaises(EditorialNormInvalid) as context:
            EditorialNormsLoader(self._editorial_norms_file_path).load()

        self.assertRegex(context.exception.dict()["error"], r"'font_size_pt'.*\[document_format\]")

    def test_raises_editorial_norm_invalid_when_font_size_tolerance_pt_is_negative(self):
        self._write_norms_with_replacement(
            "font_size_tolerance_pt = 1.0", "font_size_tolerance_pt = -0.5"
        )

        with self.assertRaises(EditorialNormInvalid) as context:
            EditorialNormsLoader(self._editorial_norms_file_path).load()

        self.assertRegex(
            context.exception.dict()["error"], r"'font_size_tolerance_pt'.*\[document_format\]"
        )

    def test_raises_editorial_norm_invalid_when_max_unjustified_paragraph_ratio_is_negative(self):
        self._write_norms_with_replacement(
            "max_unjustified_paragraph_ratio = 0.3", "max_unjustified_paragraph_ratio = -0.1"
        )

        with self.assertRaises(EditorialNormInvalid) as context:
            EditorialNormsLoader(self._editorial_norms_file_path).load()

        self.assertRegex(
            context.exception.dict()["error"],
            r"'max_unjustified_paragraph_ratio'.*\[document_format\]",
        )

    def test_raises_editorial_norm_invalid_when_max_unjustified_paragraph_ratio_exceeds_one(self):
        self._write_norms_with_replacement(
            "max_unjustified_paragraph_ratio = 0.3", "max_unjustified_paragraph_ratio = 1.1"
        )

        with self.assertRaises(EditorialNormInvalid) as context:
            EditorialNormsLoader(self._editorial_norms_file_path).load()

        self.assertRegex(
            context.exception.dict()["error"],
            r"'max_unjustified_paragraph_ratio'.*\[document_format\]",
        )

    def test_raises_editorial_norm_invalid_when_abstract_min_word_count_is_less_than_one(self):
        self._write_norms_with_replacement("min_word_count = 100", "min_word_count = 0")

        with self.assertRaises(EditorialNormInvalid) as context:
            EditorialNormsLoader(self._editorial_norms_file_path).load()

        self.assertRegex(context.exception.dict()["error"], r"'min_word_count'.*\[abstract\]")

    def test_raises_editorial_norm_invalid_when_abstract_min_word_count_exceeds_max_word_count(
        self,
    ):
        self._write_norms_with_replacement("min_word_count = 100", "min_word_count = 400")

        with self.assertRaises(EditorialNormInvalid) as context:
            EditorialNormsLoader(self._editorial_norms_file_path).load()

        self.assertRegex(context.exception.dict()["error"], r"'max_word_count'.*\[abstract\]")

    def test_raises_editorial_norm_invalid_when_keywords_min_count_is_less_than_one(self):
        self._write_norms_with_replacement("min_count = 3", "min_count = 0")

        with self.assertRaises(EditorialNormInvalid) as context:
            EditorialNormsLoader(self._editorial_norms_file_path).load()

        self.assertRegex(context.exception.dict()["error"], r"'min_count'.*\[keywords\]")

    def test_raises_editorial_norm_invalid_when_keywords_min_count_exceeds_max_count(self):
        self._write_norms_with_replacement("min_count = 3", "min_count = 7")

        with self.assertRaises(EditorialNormInvalid) as context:
            EditorialNormsLoader(self._editorial_norms_file_path).load()

        self.assertRegex(context.exception.dict()["error"], r"'max_count'.*\[keywords\]")

    def test_loads_real_project_editorial_norms_file(self):
        norms = EditorialNormsLoader(PROJECT_EDITORIAL_NORMS_PATH).load()

        self.assertEqual(norms.document_format.margin_cm, 2.5)
        self.assertEqual(norms.document_format.margin_tolerance_cm, 0.3)
        self.assertEqual(norms.document_format.font_size_pt, 12.0)
        self.assertEqual(norms.document_format.font_size_tolerance_pt, 1.0)
        self.assertEqual(
            norms.document_format.allowed_fonts, ("Times New Roman", "Arial", "Calibri")
        )
        self.assertEqual(norms.document_format.max_unjustified_paragraph_ratio, 0.3)
        self.assertEqual(norms.figure_captions.caption_prefixes, ("figura", "fig.", "figure"))
        self.assertEqual(norms.table_captions.caption_prefixes, ("tabla", "table", "cuadro"))
        self.assertEqual(
            norms.abstract.section_keywords, ("resumen", "abstract", "síntesis", "sumario")
        )
        self.assertEqual(norms.abstract.min_word_count, 100)
        self.assertEqual(norms.abstract.max_word_count, 300)
        self.assertEqual(
            norms.keywords.section_markers,
            ("palabras clave", "keywords", "key words", "descriptores"),
        )
        self.assertEqual(norms.keywords.min_count, 3)
        self.assertEqual(norms.keywords.max_count, 5)
