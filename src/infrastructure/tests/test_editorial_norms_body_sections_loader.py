from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from src.domain.dtos.article_length_norms_dto import ArticleLengthNormsDTO
from src.domain.dtos.bibliography_norms_dto import BibliographyNormsDTO
from src.domain.dtos.editorial_norms_dto import EditorialNormsDTO
from src.domain.exceptions.editorial_norms_errors import (
    EditorialNormInvalid,
    EditorialNormMissing,
)
from src.infrastructure.editorial_norms_loader import EditorialNormsLoader

BASE_NORMS_CONTENT = (
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
    "\n"
    "[required_sections]\n"
    '"científico" = ["Resumen", "Introducción", "Metodología", "Resultados", "Discusión", "Conclusiones", "Referencias"]\n'
    '"divulgación" = ["Resumen", "Introducción", "Desarrollo", "Conclusiones", "Referencias"]\n'
    '"opinión" = ["Introducción", "Argumentación", "Conclusiones"]\n'
    "\n"
    "[section_aliases]\n"
    '"Resumen" = ["resumen", "abstract"]\n'
    '"Introducción" = ["introducción", "introduccion", "introduction"]\n'
    '"Metodología" = ["metodología", "metodologia", "methodology"]\n'
    '"Resultados" = ["resultados", "results"]\n'
    '"Discusión" = ["discusión", "discusion", "discussion"]\n'
    '"Argumentación" = ["argumentación", "argumentacion", "argumentation"]\n'
    '"Desarrollo" = ["desarrollo", "development"]\n'
    '"Conclusiones" = ["conclusiones", "conclusión", "conclusion"]\n'
    '"Referencias" = ["referencias", "bibliografía", "bibliografia", "fuentes bibliográficas"]\n'
)
BIBLIOGRAPHY_MARKERS_LINE = 'header_markers = ["  Refs  ", "biblio", "REFS", "Biblio"]'
BIBLIOGRAPHY_SECTION = f"[bibliography]\n{BIBLIOGRAPHY_MARKERS_LINE}\nheader_max_length = 21\n"
ARTICLE_LENGTH_SECTION = "[article_length]\nmax_body_chars = 1234\n"


class TestEditorialNormsBodySectionsLoader(TestCase):
    def setUp(self):
        self._temporary_directory = TemporaryDirectory()
        self.addCleanup(self._temporary_directory.cleanup)
        self._editorial_norms_file_path = (
            Path(self._temporary_directory.name) / "editorial_norms.toml"
        )

    def _write_norms_content(self, content: str) -> None:
        self._editorial_norms_file_path.write_text(content, encoding="utf-8")

    def _write_valid_norms_file(self) -> None:
        self._write_norms_content(
            BASE_NORMS_CONTENT + "\n" + BIBLIOGRAPHY_SECTION + "\n" + ARTICLE_LENGTH_SECTION
        )

    def _write_norms_with_replacement(self, original_line: str, replacement_line: str) -> None:
        self._write_valid_norms_file()
        current_content = self._editorial_norms_file_path.read_text(encoding="utf-8")
        self.assertIn(original_line, current_content)
        self._write_norms_content(current_content.replace(original_line, replacement_line))

    def test_loads_bibliography_and_article_length_norms_dtos(self):
        self._write_valid_norms_file()

        norms = EditorialNormsLoader(self._editorial_norms_file_path).load()

        self.assertIsInstance(norms, EditorialNormsDTO)
        self.assertEqual(
            norms.bibliography,
            BibliographyNormsDTO(header_markers=("refs", "biblio"), header_max_length=21),
        )
        self.assertEqual(norms.article_length, ArticleLengthNormsDTO(max_body_chars=1234))

    def test_normalizes_header_markers_by_stripping_lowercasing_and_dropping_duplicates(self):
        self._write_valid_norms_file()

        norms = EditorialNormsLoader(self._editorial_norms_file_path).load()

        self.assertEqual(norms.bibliography.header_markers, ("refs", "biblio"))

    def test_loads_header_max_length_from_bibliography_section(self):
        self._write_norms_with_replacement("header_max_length = 21", "header_max_length = 40")

        norms = EditorialNormsLoader(self._editorial_norms_file_path).load()

        self.assertEqual(norms.bibliography.header_max_length, 40)

    def test_loads_max_body_chars_from_article_length_section(self):
        self._write_norms_with_replacement("max_body_chars = 1234", "max_body_chars = 75000")

        norms = EditorialNormsLoader(self._editorial_norms_file_path).load()

        self.assertEqual(norms.article_length.max_body_chars, 75000)

    def test_raises_editorial_norm_missing_when_bibliography_section_is_absent(self):
        self._write_norms_content(BASE_NORMS_CONTENT + "\n" + ARTICLE_LENGTH_SECTION)

        with self.assertRaises(EditorialNormMissing) as context:
            EditorialNormsLoader(self._editorial_norms_file_path).load()

        self.assertRegex(context.exception.dict()["error"], r"\[bibliography\]")

    def test_raises_editorial_norm_missing_when_article_length_section_is_absent(self):
        self._write_norms_content(BASE_NORMS_CONTENT + "\n" + BIBLIOGRAPHY_SECTION)

        with self.assertRaises(EditorialNormMissing) as context:
            EditorialNormsLoader(self._editorial_norms_file_path).load()

        self.assertRegex(context.exception.dict()["error"], r"\[article_length\]")

    def test_raises_editorial_norm_invalid_when_header_max_length_is_zero(self):
        self._write_norms_with_replacement("header_max_length = 21", "header_max_length = 0")

        with self.assertRaises(EditorialNormInvalid) as context:
            EditorialNormsLoader(self._editorial_norms_file_path).load()

        self.assertRegex(
            context.exception.dict()["error"], r"'header_max_length'.*\[bibliography\]"
        )

    def test_raises_editorial_norm_invalid_when_max_body_chars_is_zero(self):
        self._write_norms_with_replacement("max_body_chars = 1234", "max_body_chars = 0")

        with self.assertRaises(EditorialNormInvalid) as context:
            EditorialNormsLoader(self._editorial_norms_file_path).load()

        self.assertRegex(context.exception.dict()["error"], r"'max_body_chars'.*\[article_length\]")

    def test_raises_editorial_norm_invalid_when_header_markers_is_empty(self):
        self._write_norms_with_replacement(BIBLIOGRAPHY_MARKERS_LINE, "header_markers = []")

        with self.assertRaises(EditorialNormInvalid) as context:
            EditorialNormsLoader(self._editorial_norms_file_path).load()

        self.assertRegex(context.exception.dict()["error"], r"'header_markers'.*\[bibliography\]")
