from unittest import TestCase
from unittest.mock import MagicMock

from src.application.analyze_document_use_case import AnalyzeDocumentUseCase
from src.domain.dtos.citation_dto import CitationDTO
from src.domain.dtos.eumic_violation_dto import EumicViolationDTO
from src.domain.dtos.report_input_dto import ReportInputDTO
from src.domain.enums.article_type import ArticleType
from src.domain.enums.citation_type import CitationType


def _make_citation(text="(Smith, 2020)", citation_type=CitationType.AUTHOR_YEAR, location=0):
    return CitationDTO(text=text, citation_type=citation_type, location=location)


def _make_classification(article_type=ArticleType.POPULAR_SCIENCE, reasoning="Test"):
    m = MagicMock()
    m.article_type = article_type
    m.effective_structure_type = article_type
    m.reasoning = reasoning
    return m


def _make_extraction_result(citations=None, references=None, section_type="Referencias"):
    m = MagicMock()
    m.citations = citations if citations is not None else []
    m.references = references if references is not None else []
    m.section_type = section_type
    return m


def _make_content(word_count=2500, paragraphs=None):
    m = MagicMock()
    m.word_count = word_count
    m.paragraphs = paragraphs if paragraphs is not None else ["Para0", "Para1"]
    return m


class TestAnalyzeDocumentUseCase(TestCase):
    def _make_use_case(self, **overrides):
        read_doc = MagicMock()
        extract_content = MagicMock()
        extract_citations = MagicMock()
        validate_apa = MagicMock()
        check_grammar = MagicMock()
        classify_article = MagicMock()
        analyze_quality = MagicMock()
        validate_structure = MagicMock()
        match_citations = MagicMock()
        verify_eumic = MagicMock()
        recommendation_builder = MagicMock()

        read_doc.execute.return_value = ["Paragraph 0", "Paragraph 1"]
        extract_content.execute.return_value = _make_content()
        extract_citations.execute.return_value = _make_extraction_result()
        validate_apa.execute.return_value = MagicMock(violations=[])
        check_grammar.execute.return_value = MagicMock(score=8.0)
        classify_article.execute.return_value = _make_classification()
        analyze_quality.execute.return_value = MagicMock(overall_score=8.0)
        validate_structure.execute.return_value = MagicMock(is_valid=True, missing_sections=[])
        match_citations.execute.return_value = MagicMock(
            total_citations=5, matched_count=5, unmatched_count=0
        )
        verify_eumic.execute.return_value = []
        recommendation_builder.build.return_value = ([], MagicMock())

        mocks = {
            "read_document_use_case": read_doc,
            "extract_content_use_case": extract_content,
            "extract_citations_use_case": extract_citations,
            "validate_apa_use_case": validate_apa,
            "check_grammar_use_case": check_grammar,
            "classify_article_use_case": classify_article,
            "analyze_quality_use_case": analyze_quality,
            "validate_structure_use_case": validate_structure,
            "match_citations_use_case": match_citations,
            "verify_eumic_use_case": verify_eumic,
            "recommendation_builder": recommendation_builder,
        }
        mocks.update(overrides)
        use_case = AnalyzeDocumentUseCase(**mocks)
        return use_case, mocks

    def test_execute_returns_report_input_dto(self):
        use_case, _ = self._make_use_case()
        result = use_case.execute(document_path="test.docx")
        self.assertIsInstance(result, ReportInputDTO)

    def test_execute_calls_all_sub_use_cases_once(self):
        use_case, mocks = self._make_use_case()
        use_case.execute(document_path="test.docx")

        mocks["read_document_use_case"].execute.assert_called_once_with(path="test.docx")
        mocks["extract_content_use_case"].execute.assert_called_once()
        mocks["extract_citations_use_case"].execute.assert_called_once_with(docx_path="test.docx")
        mocks["validate_apa_use_case"].execute.assert_called_once()
        mocks["check_grammar_use_case"].execute.assert_called_once()
        mocks["classify_article_use_case"].execute.assert_called_once()
        mocks["analyze_quality_use_case"].execute.assert_called_once()
        mocks["validate_structure_use_case"].execute.assert_called_once()
        mocks["match_citations_use_case"].execute.assert_called_once()
        mocks["verify_eumic_use_case"].execute.assert_called_once()
        mocks["recommendation_builder"].build.assert_called_once()

    def test_only_author_year_citations_sent_to_validate_apa(self):
        author_year = _make_citation(
            text="(Smith, 2020)", citation_type=CitationType.AUTHOR_YEAR, location=0
        )
        numeric = _make_citation(text="[1]", citation_type=CitationType.NUMERIC, location=1)

        extract_citations = MagicMock()
        extract_citations.execute.return_value = _make_extraction_result(
            citations=[author_year, numeric],
        )

        use_case, mocks = self._make_use_case(extract_citations_use_case=extract_citations)
        use_case.execute(document_path="test.docx")

        validate_apa_call_args = mocks["validate_apa_use_case"].execute.call_args
        sent_citations = validate_apa_call_args.kwargs["citations"]
        self.assertEqual(len(sent_citations), 1)
        self.assertEqual(sent_citations[0][0], "(Smith, 2020)")

    def test_citation_tuple_includes_paragraph_text_at_location(self):
        paragraphs = ["Para 0", "Para 1", "Para 2"]
        read_doc = MagicMock()
        read_doc.execute.return_value = paragraphs

        citation = _make_citation(
            text="(Jones, 2019)", citation_type=CitationType.AUTHOR_YEAR, location=2
        )
        extract_citations = MagicMock()
        extract_citations.execute.return_value = _make_extraction_result(citations=[citation])

        use_case, mocks = self._make_use_case(
            read_document_use_case=read_doc,
            extract_citations_use_case=extract_citations,
        )
        use_case.execute(document_path="test.docx")

        sent_citations = mocks["validate_apa_use_case"].execute.call_args.kwargs["citations"]
        self.assertEqual(sent_citations[0], ("(Jones, 2019)", 2, "Para 2"))

    def test_structure_validated_with_effective_structure_type(self):
        classification = _make_classification(
            article_type=ArticleType.SCIENTIFIC,
        )
        classification.effective_structure_type = ArticleType.POPULAR_SCIENCE

        classify_article = MagicMock()
        classify_article.execute.return_value = classification

        use_case, mocks = self._make_use_case(classify_article_use_case=classify_article)
        use_case.execute(document_path="test.docx")

        validate_structure_call = mocks["validate_structure_use_case"].execute.call_args
        passed_type = validate_structure_call.kwargs["article_type"]
        self.assertEqual(passed_type, ArticleType.POPULAR_SCIENCE)

    def test_eumic_violations_included_in_report_input_dto(self):
        violation = MagicMock(spec=EumicViolationDTO)
        verify_eumic = MagicMock()
        verify_eumic.execute.return_value = [violation]

        use_case, _ = self._make_use_case(verify_eumic_use_case=verify_eumic)
        result = use_case.execute(document_path="test.docx")

        self.assertEqual(len(result.eumic_violations), 1)
        self.assertIs(result.eumic_violations[0], violation)

    def test_eumic_violations_do_not_halt_execution(self):
        violation = MagicMock(spec=EumicViolationDTO)
        verify_eumic = MagicMock()
        verify_eumic.execute.return_value = [violation]

        use_case, mocks = self._make_use_case(verify_eumic_use_case=verify_eumic)
        result = use_case.execute(document_path="test.docx")

        self.assertIsInstance(result, ReportInputDTO)
        mocks["recommendation_builder"].build.assert_called_once()

    def test_report_contains_recommendations_from_builder(self):
        use_case, _ = self._make_use_case()
        result = use_case.execute(document_path="test.docx")
        self.assertEqual(result.recommendations, [])

    def test_has_references_is_true_when_references_present(self):
        references = [MagicMock()]
        extract_citations = MagicMock()
        extract_citations.execute.return_value = _make_extraction_result(references=references)

        use_case, mocks = self._make_use_case(extract_citations_use_case=extract_citations)
        use_case.execute(document_path="test.docx")

        validate_structure_call = mocks["validate_structure_use_case"].execute.call_args
        has_ref = validate_structure_call.kwargs["has_references"]
        self.assertTrue(has_ref)

    def test_has_references_is_false_when_no_references(self):
        extract_citations = MagicMock()
        extract_citations.execute.return_value = _make_extraction_result(references=[])

        use_case, mocks = self._make_use_case(extract_citations_use_case=extract_citations)
        use_case.execute(document_path="test.docx")

        validate_structure_call = mocks["validate_structure_use_case"].execute.call_args
        has_ref = validate_structure_call.kwargs["has_references"]
        self.assertFalse(has_ref)

    def test_section_type_defaults_to_references_when_invalid(self):
        extract_citations = MagicMock()
        extract_citations.execute.return_value = _make_extraction_result(
            section_type="Invalid Section"
        )

        use_case, mocks = self._make_use_case(extract_citations_use_case=extract_citations)
        use_case.execute(document_path="test.docx")

        match_call = mocks["match_citations_use_case"].execute.call_args
        from src.domain.enums.section_name import SectionName

        section_arg = match_call.kwargs["section_type"]
        self.assertEqual(section_arg, SectionName.REFERENCES)
