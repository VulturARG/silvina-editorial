from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from src.domain.document.article_body_locator import ArticleBodyLocator
from src.infrastructure.tests.test_doubles.analyze_document_use_case_wiring_for_test import (
    AnalyzeDocumentUseCaseWiringForTest,
)
from src.infrastructure.tests.test_doubles.complete_test_settings import CompleteTestSettings


class TestArticleBodyLocatorWiring(TestCase):
    """Unit tests for the ArticleBodyLocator assembled by AnalyzeDocumentUseCaseWiring."""

    def setUp(self):
        self._temporary_directory = TemporaryDirectory()
        self.addCleanup(self._temporary_directory.cleanup)
        self._settings_file_path = Path(self._temporary_directory.name) / "settings.toml"
        self._settings_file_path.write_text(CompleteTestSettings.toml_text(), encoding="utf-8")

    def test_wiring_builds_article_body_locator(self):
        wiring = AnalyzeDocumentUseCaseWiringForTest(self._settings_file_path)

        locator = wiring._get_article_body_locator()

        self.assertIsInstance(locator, ArticleBodyLocator)

    def test_locator_closes_body_at_bibliography_marker_from_editorial_norms(self):
        wiring = AnalyzeDocumentUseCaseWiringForTest(self._settings_file_path)
        locator = wiring._get_article_body_locator()

        result = locator.locate(["Main title", "Main title", "Body one.", "Refs", "Entry."])

        self.assertEqual(result.paragraphs, ("Body one.",))

    def test_locator_ignores_bibliography_marker_that_is_not_in_editorial_norms(self):
        wiring = AnalyzeDocumentUseCaseWiringForTest(self._settings_file_path)
        locator = wiring._get_article_body_locator()

        result = locator.locate(["Main title", "Main title", "Body one.", "Referencias", "Entry."])

        self.assertEqual(result.paragraphs, ("Body one.", "Referencias", "Entry."))

    def test_locator_reads_abstract_and_keyword_markers_from_editorial_norms(self):
        wiring = AnalyzeDocumentUseCaseWiringForTest(self._settings_file_path)
        locator = wiring._get_article_body_locator()

        result = locator.locate(
            [
                "Main title",
                "Abstract",
                "Abstract sentence.",
                "Palabras clave: alpha",
                "Main title",
                "Body.",
            ]
        )

        self.assertEqual(result.abstract_paragraphs, ("Abstract sentence.",))
        self.assertEqual(result.paragraphs, ("Body.",))
