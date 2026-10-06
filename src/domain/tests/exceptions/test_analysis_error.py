from unittest import TestCase

from src.domain.exceptions.analysis_errors import AnalysisCancelled, AnalysisError
from src.domain.exceptions.base_src_error import SrcBaseWarning


class TestAnalysisError(TestCase):
    def test_is_subclass_of_src_base_warning(self):
        self.assertTrue(issubclass(AnalysisError, SrcBaseWarning))

    def test_is_parent_of_analysis_cancelled(self):
        self.assertTrue(issubclass(AnalysisCancelled, AnalysisError))

    def test_is_catchable_as_analysis_error_when_analysis_is_cancelled(self):
        with self.assertRaises(AnalysisError):
            raise AnalysisCancelled()
