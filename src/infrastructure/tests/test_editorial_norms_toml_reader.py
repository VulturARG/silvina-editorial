from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from src.domain.exceptions.editorial_norms_errors import (
    EditorialNormsFileInvalid,
    EditorialNormsFileNotFound,
)
from src.infrastructure.editorial_norms_toml_reader import EditorialNormsTomlReader


class TestEditorialNormsTomlReader(TestCase):
    def setUp(self):
        self._temporary_directory = TemporaryDirectory()
        self.addCleanup(self._temporary_directory.cleanup)
        self._editorial_norms_file_path = (
            Path(self._temporary_directory.name) / "editorial_norms.toml"
        )

    def test_loads_sections_with_typed_values(self):
        self._editorial_norms_file_path.write_text(
            '[document_format]\nmargin_cm = 2.5\nfont_size_pt = 12\nallowed_fonts = ["Arial"]\n',
            encoding="utf-8",
        )

        norms = EditorialNormsTomlReader(self._editorial_norms_file_path).load()

        self.assertEqual(
            norms,
            {
                "document_format": {
                    "margin_cm": 2.5,
                    "font_size_pt": 12,
                    "allowed_fonts": ["Arial"],
                }
            },
        )

    def test_loads_utf8_content(self):
        self._editorial_norms_file_path.write_text(
            '[abstract]\nsection_keywords = ["síntesis"]\n',
            encoding="utf-8",
        )

        norms = EditorialNormsTomlReader(self._editorial_norms_file_path).load()

        self.assertEqual(norms["abstract"]["section_keywords"], ["síntesis"])

    def test_raises_editorial_norms_file_not_found_naming_the_path_when_file_is_missing(self):
        reader = EditorialNormsTomlReader(self._editorial_norms_file_path)

        with self.assertRaises(EditorialNormsFileNotFound) as context:
            reader.load()

        self.assertIn(str(self._editorial_norms_file_path), context.exception.dict()["error"])

    def test_raises_editorial_norms_file_invalid_naming_the_path_when_toml_is_malformed(self):
        self._editorial_norms_file_path.write_text(
            "[document_format\nmargin_cm = ",
            encoding="utf-8",
        )
        reader = EditorialNormsTomlReader(self._editorial_norms_file_path)

        with self.assertRaises(EditorialNormsFileInvalid) as context:
            reader.load()

        self.assertIn(str(self._editorial_norms_file_path), context.exception.dict()["error"])
