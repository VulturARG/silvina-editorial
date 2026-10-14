from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from src.infrastructure.cli.report_file_paths_builder import ReportFilePathsBuilder
from src.infrastructure.cli.windows_file_name_sanitizer import WindowsFileNameSanitizer


class TestReportFilePathsBuilder(TestCase):
    DOCUMENT_PATH = Path("C:/docs/tesis.docx")

    def setUp(self):
        self.builder = ReportFilePathsBuilder(file_name_sanitizer=WindowsFileNameSanitizer())
        temporary_directory = TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        self.temporary_directory = Path(temporary_directory.name)

    def test_default_directory_is_analisis_folder_next_to_document(self):
        paths = self.builder.build(self.DOCUMENT_PATH, None, "gemma")

        self.assertEqual(paths.word_path.parent, Path("C:/docs") / "análisis")

    def test_explicit_output_directory_is_used_as_given(self):
        output_directory = Path("D:/salida/informes")

        paths = self.builder.build(self.DOCUMENT_PATH, output_directory, "gemma")

        self.assertEqual(paths.word_path.parent, output_directory)
        self.assertEqual(paths.json_path.parent, output_directory)
        self.assertEqual(paths.html_path.parent, output_directory)

    def test_three_paths_share_base_name_and_use_their_extensions(self):
        output_directory = Path("D:/salida")

        paths = self.builder.build(self.DOCUMENT_PATH, output_directory, "gemma")

        self.assertEqual(paths.word_path, output_directory / "tesis_analisis_gemma.docx")
        self.assertEqual(paths.json_path, output_directory / "tesis_analisis_gemma.json")
        self.assertEqual(paths.html_path, output_directory / "tesis_analisis_gemma.html")

    def test_model_name_slashes_and_colons_are_sanitized(self):
        output_directory = Path("D:/salida")

        paths = self.builder.build(
            self.DOCUMENT_PATH, output_directory, "hf.co/unsloth/gemma:UD-IQ4"
        )

        self.assertEqual(
            paths.word_path,
            output_directory / "tesis_analisis_hf.co_unsloth_gemma_UD-IQ4.docx",
        )

    def test_empty_model_name_omits_model_suffix(self):
        output_directory = Path("D:/salida")

        paths = self.builder.build(self.DOCUMENT_PATH, output_directory, "")

        self.assertEqual(paths.word_path, output_directory / "tesis_analisis.docx")
        self.assertEqual(paths.json_path, output_directory / "tesis_analisis.json")
        self.assertEqual(paths.html_path, output_directory / "tesis_analisis.html")

    def test_document_stem_with_invalid_characters_is_sanitized(self):
        output_directory = Path("D:/salida")
        document_path = Path("C:/docs/tesis|v2.docx")

        paths = self.builder.build(document_path, output_directory, "gemma")

        self.assertEqual(paths.word_path, output_directory / "tesis_v2_analisis_gemma.docx")

    def test_building_paths_creates_no_default_output_directory(self):
        document_path = self.temporary_directory / "tesis.docx"

        self.builder.build(document_path, None, "gemma")

        self.assertFalse((self.temporary_directory / "análisis").exists())

    def test_building_paths_creates_no_explicit_output_directory(self):
        output_directory = self.temporary_directory / "salida"
        document_path = self.temporary_directory / "tesis.docx"

        self.builder.build(document_path, output_directory, "gemma")

        self.assertFalse(output_directory.exists())
