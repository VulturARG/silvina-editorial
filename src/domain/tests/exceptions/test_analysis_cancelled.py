from unittest import TestCase

from src.domain.exceptions.analysis_errors import AnalysisCancelled, AnalysisError
from src.domain.exceptions.base_src_error import BaseSrcError, SrcBaseWarning


class TestAnalysisCancelled(TestCase):
    def test_is_subclass_of_analysis_error(self) -> None:
        self.assertTrue(issubclass(AnalysisCancelled, AnalysisError))

    def test_is_subclass_of_src_base_warning(self) -> None:
        self.assertTrue(issubclass(AnalysisCancelled, SrcBaseWarning))

    def test_is_subclass_of_base_src_error(self) -> None:
        self.assertTrue(issubclass(AnalysisCancelled, BaseSrcError))

    def test_has_expected_error_message(self) -> None:
        error = AnalysisCancelled()
        self.assertEqual(
            error.dict(),
            {"error": "The analysis was cancelled because the client disconnected."},
        )

    def test_default_message_attribute(self) -> None:
        self.assertEqual(
            AnalysisCancelled.MESSAGE,
            "The analysis was cancelled because the client disconnected.",
        )

    def test_is_catchable_as_src_base_warning(self) -> None:
        with self.assertRaises(SrcBaseWarning):
            raise AnalysisCancelled()
