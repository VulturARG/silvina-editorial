from unittest import TestCase
from unittest.mock import MagicMock

from src.application.analyze_document_use_case import AnalyzeDocumentUseCase
from src.domain.dtos.eumic_violation_dto import EumicViolationDTO
from src.domain.dtos.report_input_dto import ReportInputDTO
from src.domain.dtos.structure_validation_result_dto import StructureValidationResultDTO
from src.domain.enums.article_type import ArticleType


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
        laya_decision_maker = MagicMock()
        article_classifier = MagicMock()
        quality_analyzer = MagicMock()
        structure_validator = MagicMock()
        citation_matcher = MagicMock()
        recommendation_builder = MagicMock()

        document_content_extractor.extract_content.return_value = _make_content()
        citation_extractor.extract_citations_and_references.return_value = ([], [], "Referencias")
        apa_validator.validate_all_citations.return_value = []
        grammar_checker.check_grammar.return_value = MagicMock()
        laya_decision_maker.decide.return_value = MagicMock()
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
            "laya_decision_maker": laya_decision_maker,
            "article_classifier": article_classifier,
            "quality_analyzer": quality_analyzer,
            "structure_validator": structure_validator,
            "citation_matcher": citation_matcher,
            "recommendation_builder": recommendation_builder,
        }
        mocks.update(overrides)
        use_case = AnalyzeDocumentUseCase(**mocks)
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
        mocks["laya_decision_maker"].decide.assert_called_once()
        mocks["article_classifier"].classify.assert_called_once()
        mocks["quality_analyzer"].analyze.assert_called_once()
        mocks["structure_validator"].validate_structure.assert_called_once()
        mocks["citation_matcher"].match_citations_to_references.assert_called_once()
        mocks["document_format_inspector"].inspect.assert_called_once()
        mocks["recommendation_builder"].build.assert_called_once()

    def test_laya_decision_is_made_once_from_the_document_content(self):
        use_case, mocks = self._make_use_case()
        use_case.execute(document_path="test.docx")

        mocks["laya_decision_maker"].decide.assert_called_once_with(
            document_content=mocks["document_content_extractor"].extract_content.return_value
        )

    def test_article_classifier_receives_the_laya_decision(self):
        use_case, mocks = self._make_use_case()
        use_case.execute(document_path="test.docx")

        mocks["article_classifier"].classify.assert_called_once_with(
            document_content=mocks["document_content_extractor"].extract_content.return_value,
            laya_decision=mocks["laya_decision_maker"].decide.return_value,
        )

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

        from src.domain.enums.section_name import SectionName

        match_call = mocks["citation_matcher"].match_citations_to_references.call_args
        self.assertEqual(match_call.kwargs["section_type"], SectionName.REFERENCES)

    def test_structure_result_returned_directly_from_validator(self):
        expected = StructureValidationResultDTO(is_valid=False, missing_sections=[])
        structure_validator = MagicMock()
        structure_validator.validate_structure.return_value = expected

        use_case, _ = self._make_use_case(structure_validator=structure_validator)
        result = use_case.execute(document_path="test.docx")

        self.assertIs(result.structure, expected)
