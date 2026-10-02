from unittest import TestCase
from unittest.mock import MagicMock

from src.application.analyze_document_use_case import AnalyzeDocumentUseCase
from src.domain.dtos.eumic_violation_dto import EumicViolationDTO
from src.domain.dtos.report_input_dto import ReportInputDTO
from src.domain.dtos.structure_validation_result_dto import StructureValidationResultDTO
from src.domain.enums.analysis_stage import AnalysisStage
from src.domain.enums.article_type import ArticleType
from src.domain.enums.execution_status import ExecutionStatus
from src.domain.enums.section_name import SectionName
from src.domain.exceptions.base_src_error import SrcGenericError
from src.domain.metrics.analysis_metrics_recorder import AnalysisMetricsRecorder
from src.domain.metrics.analysis_tracker import AnalysisTracker
from src.domain.tests.metrics.fake_analysis_context_port import FakeAnalysisContextPort
from src.domain.tests.metrics.fake_analysis_metrics_port import FakeAnalysisMetricsPort


def _make_classification(article_type=ArticleType.POPULAR_SCIENCE, reasoning="Test"):
    m = MagicMock()
    m.article_type = article_type
    m.effective_structure_type = article_type
    m.reasoning = reasoning
    return m


def _make_content(word_count=2500, paragraphs=None):
    m = MagicMock()
    m.word_count = word_count
    m.paragraphs = paragraphs if paragraphs is not None else ["Para0", "Para1"]
    return m


class TestAnalyzeDocumentUseCase(TestCase):
    def _make_use_case(self, **overrides):
        document_content_extractor = MagicMock()
        citation_extractor = MagicMock()
        document_format_inspector = MagicMock()
        grammar_checker = MagicMock()
        apa_validator = MagicMock()
        article_classifier = MagicMock()
        quality_analyzer = MagicMock()
        structure_validator = MagicMock()
        citation_matcher = MagicMock()
        recommendation_builder = MagicMock()

        fake_metrics_port = overrides.pop("fake_metrics_port", FakeAnalysisMetricsPort())
        fake_context_port = overrides.pop("fake_context_port", FakeAnalysisContextPort())
        metrics_recorder = overrides.pop(
            "metrics_recorder",
            AnalysisMetricsRecorder(metrics_port=fake_metrics_port),
        )
        analysis_tracker = overrides.pop(
            "analysis_tracker",
            AnalysisTracker(
                metrics_recorder=metrics_recorder,
                analysis_context_port=fake_context_port,
            ),
        )

        document_content_extractor.extract_content.return_value = _make_content()
        citation_extractor.extract_citations_and_references.return_value = ([], [], "Referencias")
        apa_validator.validate_all_citations.return_value = []
        grammar_checker.check_grammar.return_value = MagicMock()
        article_classifier.classify.return_value = _make_classification()
        quality_analyzer.analyze.return_value = MagicMock(overall_score=8.0)
        structure_validator.validate_structure.return_value = StructureValidationResultDTO(
            is_valid=True, missing_sections=[]
        )
        citation_matcher.match_citations_to_references.return_value = MagicMock(
            total_citations=5, matched_count=5, unmatched_count=0
        )
        document_format_inspector.inspect.return_value = []
        recommendation_builder.build.return_value = ([], MagicMock())

        mocks = {
            "document_content_extractor": document_content_extractor,
            "citation_extractor": citation_extractor,
            "document_format_inspector": document_format_inspector,
            "grammar_checker": grammar_checker,
            "apa_validator": apa_validator,
            "article_classifier": article_classifier,
            "quality_analyzer": quality_analyzer,
            "structure_validator": structure_validator,
            "citation_matcher": citation_matcher,
            "recommendation_builder": recommendation_builder,
            "analysis_tracker": analysis_tracker,
            "fake_metrics_port": fake_metrics_port,
            "fake_context_port": fake_context_port,
        }
        mocks.update(overrides)
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
            analysis_tracker=mocks["analysis_tracker"],
        )
        return use_case, mocks

    def test_execute_returns_report_input_dto(self):
        use_case, _ = self._make_use_case()
        result = use_case.execute(document_path="test.docx")
        self.assertIsInstance(result, ReportInputDTO)

    def test_execute_calls_all_domain_services_once(self):
        use_case, mocks = self._make_use_case()
        use_case.execute(document_path="test.docx")

        mocks["document_content_extractor"].extract_content.assert_called_once_with(
            docx_path="test.docx"
        )
        mocks["citation_extractor"].extract_citations_and_references.assert_called_once_with(
            docx_path="test.docx"
        )
        mocks["apa_validator"].validate_all_citations.assert_called_once()
        mocks["grammar_checker"].check_grammar.assert_called_once()
        mocks["article_classifier"].classify.assert_called_once()
        mocks["quality_analyzer"].analyze.assert_called_once()
        mocks["structure_validator"].validate_structure.assert_called_once()
        mocks["citation_matcher"].match_citations_to_references.assert_called_once()
        mocks["document_format_inspector"].inspect.assert_called_once()
        mocks["recommendation_builder"].build.assert_called_once()

    def test_apa_validator_receives_citations_and_document_paragraphs(self):
        content = _make_content(paragraphs=["Para 0", "Para 1", "Para 2"])
        document_content_extractor = MagicMock()
        document_content_extractor.extract_content.return_value = content

        citations = [MagicMock(), MagicMock()]
        citation_extractor = MagicMock()
        citation_extractor.extract_citations_and_references.return_value = (
            citations,
            [],
            "Referencias",
        )

        use_case, mocks = self._make_use_case(
            document_content_extractor=document_content_extractor,
            citation_extractor=citation_extractor,
        )
        use_case.execute(document_path="test.docx")

        call_kwargs = mocks["apa_validator"].validate_all_citations.call_args.kwargs
        self.assertEqual(call_kwargs["citations"], citations)
        self.assertEqual(call_kwargs["paragraphs"], content.paragraphs)

    def test_structure_validated_with_effective_structure_type(self):
        classification = _make_classification(article_type=ArticleType.SCIENTIFIC)
        classification.effective_structure_type = ArticleType.POPULAR_SCIENCE

        article_classifier = MagicMock()
        article_classifier.classify.return_value = classification

        use_case, mocks = self._make_use_case(article_classifier=article_classifier)
        use_case.execute(document_path="test.docx")

        validate_call = mocks["structure_validator"].validate_structure.call_args
        self.assertEqual(validate_call.kwargs["article_type"], ArticleType.POPULAR_SCIENCE)

    def test_eumic_violations_included_in_report_input_dto(self):
        violation = MagicMock(spec=EumicViolationDTO)
        document_format_inspector = MagicMock()
        document_format_inspector.inspect.return_value = [violation]

        use_case, _ = self._make_use_case(document_format_inspector=document_format_inspector)
        result = use_case.execute(document_path="test.docx")

        self.assertEqual(len(result.eumic_violations), 1)
        self.assertIs(result.eumic_violations[0], violation)

    def test_eumic_violations_do_not_halt_execution(self):
        violation = MagicMock(spec=EumicViolationDTO)
        document_format_inspector = MagicMock()
        document_format_inspector.inspect.return_value = [violation]

        use_case, mocks = self._make_use_case(document_format_inspector=document_format_inspector)
        result = use_case.execute(document_path="test.docx")

        self.assertIsInstance(result, ReportInputDTO)
        mocks["recommendation_builder"].build.assert_called_once()

    def test_report_contains_recommendations_from_builder(self):
        use_case, _ = self._make_use_case()
        result = use_case.execute(document_path="test.docx")
        self.assertEqual(result.recommendations, [])

    def test_has_references_true_when_references_present(self):
        citation_extractor = MagicMock()
        citation_extractor.extract_citations_and_references.return_value = (
            [],
            [MagicMock()],
            "Referencias",
        )

        use_case, mocks = self._make_use_case(citation_extractor=citation_extractor)
        use_case.execute(document_path="test.docx")

        validate_call = mocks["structure_validator"].validate_structure.call_args
        self.assertTrue(validate_call.kwargs["has_references"])

    def test_has_references_false_when_no_references(self):
        citation_extractor = MagicMock()
        citation_extractor.extract_citations_and_references.return_value = ([], [], "Referencias")

        use_case, mocks = self._make_use_case(citation_extractor=citation_extractor)
        use_case.execute(document_path="test.docx")

        validate_call = mocks["structure_validator"].validate_structure.call_args
        self.assertFalse(validate_call.kwargs["has_references"])

    def test_section_type_defaults_to_references_when_invalid(self):
        citation_extractor = MagicMock()
        citation_extractor.extract_citations_and_references.return_value = (
            [],
            [],
            "Invalid Section",
        )

        use_case, mocks = self._make_use_case(citation_extractor=citation_extractor)
        use_case.execute(document_path="test.docx")

        match_call = mocks["citation_matcher"].match_citations_to_references.call_args
        self.assertEqual(match_call.kwargs["section_type"], SectionName.REFERENCES)

    def test_structure_result_returned_directly_from_validator(self):
        expected = StructureValidationResultDTO(is_valid=False, missing_sections=[])
        structure_validator = MagicMock()
        structure_validator.validate_structure.return_value = expected

        use_case, _ = self._make_use_case(structure_validator=structure_validator)
        result = use_case.execute(document_path="test.docx")

        self.assertIs(result.structure, expected)

    def test_execute_records_telemetry_for_start_stages_and_successful_completion(self):
        use_case, mocks = self._make_use_case()
        result = use_case.execute(document_path="test.docx")

        fake_metrics_port: FakeAnalysisMetricsPort = mocks["fake_metrics_port"]
        self.assertEqual(len(fake_metrics_port.recorded_starts), 1)
        start_event = fake_metrics_port.recorded_starts[0]
        self.assertEqual(start_event.document_name, "test.docx")

        expected_stages = [
            AnalysisStage.EXTRACT_CONTENT,
            AnalysisStage.EXTRACT_CITATIONS,
            AnalysisStage.VALIDATE_APA,
            AnalysisStage.CHECK_GRAMMAR,
            AnalysisStage.CLASSIFY_ARTICLE,
            AnalysisStage.ANALYZE_QUALITY,
            AnalysisStage.VALIDATE_STRUCTURE,
            AnalysisStage.MATCH_CITATIONS,
            AnalysisStage.INSPECT_FORMAT,
            AnalysisStage.BUILD_RECOMMENDATIONS,
        ]
        self.assertEqual(len(fake_metrics_port.recorded_stage_durations), 10)
        recorded_stages = [
            stage_event.stage_name for stage_event in fake_metrics_port.recorded_stage_durations
        ]
        self.assertEqual(recorded_stages, expected_stages)

        for stage_event in fake_metrics_port.recorded_stage_durations:
            self.assertEqual(stage_event.analysis_id, start_event.analysis_id)
            self.assertGreaterEqual(stage_event.duration_ms, 0)

        self.assertEqual(len(fake_metrics_port.recorded_completions), 1)
        completion_event = fake_metrics_port.recorded_completions[0]
        self.assertEqual(completion_event.analysis_id, start_event.analysis_id)
        self.assertEqual(completion_event.document_name, "test.docx")
        self.assertEqual(completion_event.status, ExecutionStatus.SUCCESS)
        self.assertEqual(completion_event.word_count, result.document_content.word_count)
        self.assertEqual(completion_event.char_count, result.document_content.char_count)
        self.assertEqual(
            completion_event.article_type, result.classification.effective_structure_type
        )
        self.assertEqual(completion_event.verdict, result.verdict.verdict)
        self.assertGreaterEqual(completion_event.total_duration_ms, 0)

    def test_analysis_id_is_accessible_to_collaborators_during_pipeline_and_cleared_afterwards(
        self,
    ):
        captured_analysis_id = None
        fake_context_port = FakeAnalysisContextPort()

        def capture_analysis_id(*args, **kwargs):
            nonlocal captured_analysis_id
            captured_analysis_id = fake_context_port.get_analysis_id()
            return _make_classification()

        article_classifier = MagicMock()
        article_classifier.classify.side_effect = capture_analysis_id

        use_case, mocks = self._make_use_case(
            fake_context_port=fake_context_port,
            article_classifier=article_classifier,
        )
        use_case.execute(document_path="test.docx")

        fake_metrics_port: FakeAnalysisMetricsPort = mocks["fake_metrics_port"]
        active_analysis_id = fake_metrics_port.recorded_starts[0].analysis_id
        self.assertIsNotNone(captured_analysis_id)
        self.assertEqual(captured_analysis_id, active_analysis_id)
        self.assertIsNone(fake_context_port.get_analysis_id())

    def test_execute_records_failure_telemetry_and_clears_context_when_stage_fails(self):
        grammar_checker = MagicMock()
        grammar_checker.check_grammar.side_effect = ValueError("Syntax inspection failed")

        use_case, mocks = self._make_use_case(grammar_checker=grammar_checker)
        fake_metrics_port: FakeAnalysisMetricsPort = mocks["fake_metrics_port"]
        fake_context_port: FakeAnalysisContextPort = mocks["fake_context_port"]

        with self.assertRaises(SrcGenericError):
            use_case.execute(document_path="test.docx")

        self.assertEqual(len(fake_metrics_port.recorded_starts), 1)
        active_analysis_id = fake_metrics_port.recorded_starts[0].analysis_id

        recorded_stages = [
            stage_event.stage_name for stage_event in fake_metrics_port.recorded_stage_durations
        ]
        expected_stages = [
            AnalysisStage.EXTRACT_CONTENT,
            AnalysisStage.EXTRACT_CITATIONS,
            AnalysisStage.VALIDATE_APA,
            AnalysisStage.CHECK_GRAMMAR,
        ]
        self.assertEqual(recorded_stages, expected_stages)

        self.assertEqual(len(fake_metrics_port.recorded_completions), 1)
        completion_event = fake_metrics_port.recorded_completions[0]
        self.assertEqual(completion_event.analysis_id, active_analysis_id)
        self.assertEqual(completion_event.status, ExecutionStatus.ERROR)
        self.assertIsNone(completion_event.word_count)
        self.assertIsNone(completion_event.char_count)
        self.assertIsNone(completion_event.article_type)
        self.assertIsNone(completion_event.verdict)
        self.assertGreaterEqual(completion_event.total_duration_ms, 0)
        self.assertIsNone(fake_context_port.get_analysis_id())

    def test_execute_records_base_name_as_document_name(self):
        use_case, mocks = self._make_use_case()
        use_case.execute(document_path="/nested/directory/path/manuscript.docx")

        fake_metrics_port: FakeAnalysisMetricsPort = mocks["fake_metrics_port"]
        self.assertEqual(fake_metrics_port.recorded_starts[0].document_name, "manuscript.docx")
        self.assertEqual(fake_metrics_port.recorded_completions[0].document_name, "manuscript.docx")

    def test_execute_with_custom_document_name_uses_it_for_metrics_and_report(self):
        use_case, mocks = self._make_use_case()
        result = use_case.execute(
            document_path="/temp/path/upload_tmp123.docx",
            document_name="original_manuscript.docx",
        )

        self.assertEqual(result.filename, "original_manuscript.docx")
        mocks["document_content_extractor"].extract_content.assert_called_once_with(
            docx_path="/temp/path/upload_tmp123.docx"
        )
        mocks["citation_extractor"].extract_citations_and_references.assert_called_once_with(
            docx_path="/temp/path/upload_tmp123.docx"
        )
        mocks["document_format_inspector"].inspect.assert_called_once_with(
            docx_path="/temp/path/upload_tmp123.docx",
            word_count=result.document_content.word_count,
        )

        fake_metrics_port: FakeAnalysisMetricsPort = mocks["fake_metrics_port"]
        self.assertEqual(
            fake_metrics_port.recorded_starts[0].document_name,
            "original_manuscript.docx",
        )
        self.assertEqual(
            fake_metrics_port.recorded_completions[0].document_name,
            "original_manuscript.docx",
        )

    def test_execute_without_document_name_falls_back_to_document_path(self):
        use_case, mocks = self._make_use_case()
        result = use_case.execute(document_path="/nested/path/manuscript.docx")

        self.assertEqual(result.filename, "/nested/path/manuscript.docx")
        fake_metrics_port: FakeAnalysisMetricsPort = mocks["fake_metrics_port"]
        self.assertEqual(fake_metrics_port.recorded_starts[0].document_name, "manuscript.docx")
        self.assertEqual(fake_metrics_port.recorded_completions[0].document_name, "manuscript.docx")
