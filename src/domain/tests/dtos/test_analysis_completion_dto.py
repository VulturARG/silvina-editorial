from dataclasses import FrozenInstanceError
from unittest import TestCase

from src.domain.dtos.analysis_completion_dto import AnalysisCompletionDTO
from src.domain.dtos.base_dto import BaseDTO
from src.domain.enums.article_type import ArticleType
from src.domain.enums.execution_status import ExecutionStatus
from src.domain.enums.publication_verdict import PublicationVerdict


class TestAnalysisCompletionDTO(TestCase):
    def test_is_subclass_of_base_dto(self):
        self.assertTrue(issubclass(AnalysisCompletionDTO, BaseDTO))

    def test_frozen_raises_on_mutation(self):
        completion_data = AnalysisCompletionDTO(
            analysis_id="analysis-123",
            document_name="doc.docx",
            word_count=1200,
            char_count=7500,
            article_type=ArticleType.SCIENTIFIC,
            verdict=PublicationVerdict.APPROVED,
            total_duration_ms=1850.2,
            status=ExecutionStatus.SUCCESS,
        )
        field_name = "verdict"
        with self.assertRaises(FrozenInstanceError):
            setattr(completion_data, field_name, PublicationVerdict.CRITICAL)

    def test_holds_expected_attributes(self):
        completion_data = AnalysisCompletionDTO(
            analysis_id="analysis-123",
            document_name="doc.docx",
            word_count=1200,
            char_count=7500,
            article_type=ArticleType.SCIENTIFIC,
            verdict=PublicationVerdict.APPROVED,
            total_duration_ms=1850.2,
            status=ExecutionStatus.SUCCESS,
        )
        self.assertEqual(completion_data.analysis_id, "analysis-123")
        self.assertEqual(completion_data.document_name, "doc.docx")
        self.assertEqual(completion_data.word_count, 1200)
        self.assertEqual(completion_data.char_count, 7500)
        self.assertEqual(completion_data.article_type, ArticleType.SCIENTIFIC)
        self.assertEqual(completion_data.verdict, PublicationVerdict.APPROVED)
        self.assertEqual(completion_data.total_duration_ms, 1850.2)
        self.assertEqual(completion_data.status, ExecutionStatus.SUCCESS)

    def test_holds_none_values_for_optional_fields_on_failure(self):
        completion_data = AnalysisCompletionDTO(
            analysis_id="analysis-failed-123",
            document_name="doc.docx",
            word_count=None,
            char_count=None,
            article_type=None,
            verdict=None,
            total_duration_ms=45.0,
            status=ExecutionStatus.ERROR,
        )
        self.assertEqual(completion_data.analysis_id, "analysis-failed-123")
        self.assertEqual(completion_data.document_name, "doc.docx")
        self.assertIsNone(completion_data.word_count)
        self.assertIsNone(completion_data.char_count)
        self.assertIsNone(completion_data.article_type)
        self.assertIsNone(completion_data.verdict)
        self.assertEqual(completion_data.total_duration_ms, 45.0)
        self.assertEqual(completion_data.status, ExecutionStatus.ERROR)
