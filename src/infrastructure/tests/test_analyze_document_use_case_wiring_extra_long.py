from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from src.domain.enums.article_size import ArticleSize
from src.domain.tests.dtos.editorial_norms_builder_for_test import build_editorial_norms_for_test
from src.infrastructure.tests.test_doubles.analyze_document_use_case_wiring_for_test import (
    AnalyzeDocumentUseCaseWiringForTest,
)
from src.infrastructure.tests.test_doubles.complete_test_settings import CompleteTestSettings

MAXIMUM_BODY_CHARACTERS = 61234


class TestAnalyzeDocumentUseCaseWiringExtraLong(TestCase):
    """Verifies the extra-long upper end assembled by AnalyzeDocumentUseCaseWiring."""

    def setUp(self):
        self._temporary_directory = TemporaryDirectory()
        self.addCleanup(self._temporary_directory.cleanup)
        self._settings_file_path = Path(self._temporary_directory.name) / "settings.toml"
        self._settings_file_path.write_text(CompleteTestSettings.toml_text(), encoding="utf-8")
        self._editorial_norms = build_editorial_norms_for_test(
            maximum_body_characters=MAXIMUM_BODY_CHARACTERS
        )

    def test_extra_long_upper_end_is_editorial_norms_max_body_chars(self):
        wiring = AnalyzeDocumentUseCaseWiringForTest(self._settings_file_path)

        with patch.object(
            AnalyzeDocumentUseCaseWiringForTest,
            "_get_editorial_norms",
            return_value=self._editorial_norms,
        ):
            thresholds = wiring._get_article_size_thresholds()

        self.assertEqual(thresholds.extra_long_max_chars, MAXIMUM_BODY_CHARACTERS)

    def test_size_classifier_built_by_wiring_accepts_up_to_editorial_norms_max_body_chars(self):
        wiring = AnalyzeDocumentUseCaseWiringForTest(self._settings_file_path)

        with patch.object(
            AnalyzeDocumentUseCaseWiringForTest,
            "_get_editorial_norms",
            return_value=self._editorial_norms,
        ):
            size_classifier = wiring._get_article_size_classifier()

        self.assertEqual(size_classifier.classify(MAXIMUM_BODY_CHARACTERS), ArticleSize.EXTRA_LONG)
        self.assertEqual(
            size_classifier.classify(MAXIMUM_BODY_CHARACTERS + 1), ArticleSize.OUT_OF_RANGE
        )
