from unittest import TestCase
from unittest.mock import MagicMock

from src.application.analyze_document_use_case import AnalyzeDocumentUseCase
from src.domain.enums.analysis_stage import AnalysisStage
from src.domain.exceptions.document_errors import DocumentBodyTooLong
from src.domain.metrics.analysis_metrics_recorder import AnalysisMetricsRecorder
from src.domain.metrics.analysis_tracker import AnalysisTracker
from src.domain.tests.metrics.fake_analysis_cancellation_port import (
    FakeAnalysisCancellationPort,
)
from src.domain.tests.metrics.fake_analysis_context_port import FakeAnalysisContextPort
from src.domain.tests.metrics.fake_analysis_metrics_port import FakeAnalysisMetricsPort

LATER_COLLABORATOR_NAMES = (
    "citation_extractor",
    "apa_validator",
    "grammar_checker",
    "article_classifier",
    "quality_analyzer",
    "structure_validator",
    "citation_matcher",
    "document_format_inspector",
    "recommendation_builder",
)


class TestAnalyzeDocumentUseCaseArticleLength(TestCase):
    def test_article_length_stage_is_tracked_right_after_extract_content(self):
        use_case, _, fake_metrics_port = self._build_use_case(article_length_checker=MagicMock())

        use_case.execute(document_path="test.docx")

        recorded_stages = [event.stage_name for event in fake_metrics_port.recorded_stage_durations]
        self.assertEqual(
            recorded_stages[:2],
            [AnalysisStage.EXTRACT_CONTENT, AnalysisStage.VALIDATE_ARTICLE_LENGTH],
        )

    def test_article_length_checker_receives_the_extracted_document_content(self):
        use_case, mocks, _ = self._build_use_case(article_length_checker=MagicMock())

        use_case.execute(document_path="test.docx")

        mocks["article_length_checker"].check.assert_called_once_with(
            document_content=mocks["document_content_extractor"].extract_content.return_value
        )

    def test_stops_before_later_stages_when_body_is_too_long(self):
        article_length_checker = MagicMock()
        article_length_checker.check.side_effect = DocumentBodyTooLong(
            body_characters=80000, maximum_body_characters=75000
        )
        use_case, mocks, fake_metrics_port = self._build_use_case(
            article_length_checker=article_length_checker
        )

        with self.assertRaises(DocumentBodyTooLong):
            use_case.execute(document_path="test.docx")

        for collaborator_name in LATER_COLLABORATOR_NAMES:
            with self.subTest(collaborator=collaborator_name):
                self.assertEqual(mocks[collaborator_name].mock_calls, [])

        recorded_stages = [event.stage_name for event in fake_metrics_port.recorded_stage_durations]
        self.assertEqual(
            recorded_stages,
            [AnalysisStage.EXTRACT_CONTENT, AnalysisStage.VALIDATE_ARTICLE_LENGTH],
        )

    def _build_use_case(self, article_length_checker):
        fake_metrics_port = FakeAnalysisMetricsPort()
        analysis_tracker = AnalysisTracker(
            metrics_recorder=AnalysisMetricsRecorder(metrics_port=fake_metrics_port),
            analysis_context_port=FakeAnalysisContextPort(),
            analysis_cancellation_port=FakeAnalysisCancellationPort(),
        )
        mocks = {
            "document_content_extractor": MagicMock(),
            "citation_extractor": MagicMock(),
            "document_format_inspector": MagicMock(),
            "grammar_checker": MagicMock(),
            "apa_validator": MagicMock(),
            "article_classifier": MagicMock(),
            "quality_analyzer": MagicMock(),
            "structure_validator": MagicMock(),
            "citation_matcher": MagicMock(),
            "recommendation_builder": MagicMock(),
            "article_length_checker": article_length_checker,
        }
        mocks["document_content_extractor"].extract_content.return_value = MagicMock(
            word_count=2500, paragraphs=["Para0", "Para1"]
        )
        mocks["citation_extractor"].extract_citations_and_references.return_value = (
            [],
            [],
            "Referencias",
        )
        mocks["apa_validator"].validate_all_citations.return_value = []
        mocks["article_classifier"].classify.return_value = MagicMock()
        mocks["recommendation_builder"].build.return_value = ([], MagicMock())
        mocks["document_format_inspector"].inspect.return_value = []

        use_case = AnalyzeDocumentUseCase(
            document_content_extractor=mocks["document_content_extractor"],
            citation_extractor=mocks["citation_extractor"],
            document_format_inspector=mocks["document_format_inspector"],
            grammar_checker=mocks["grammar_checker"],
            apa_validator=mocks["apa_validator"],
            article_classifier=mocks["article_classifier"],
            quality_analyzer=mocks["quality_analyzer"],
            structure_validator=mocks["structure_validator"],
            citation_matcher=mocks["citation_matcher"],
            recommendation_builder=mocks["recommendation_builder"],
            analysis_tracker=analysis_tracker,
            article_length_checker=mocks["article_length_checker"],
        )
        return use_case, mocks, fake_metrics_port
