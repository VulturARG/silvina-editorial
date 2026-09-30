from dataclasses import FrozenInstanceError
from unittest import TestCase

from src.domain.dtos.analysis_completion_dto import AnalysisCompletionDTO
from src.domain.dtos.base_dto import BaseDTO


class TestAnalysisCompletionDTO(TestCase):
    def test_is_subclass_of_base_dto(self):
        self.assertTrue(issubclass(AnalysisCompletionDTO, BaseDTO))

    def test_frozen_raises_on_mutation(self):
        completion_data = AnalysisCompletionDTO(
            analysis_id="analysis-123",
            document_name="doc.docx",
            word_count=1200,
            char_count=7500,
            article_type="Científico",
            verdict="PUBLICABLE",
            total_duration_ms=1850.2,
            status="completed",
        )
        field_name = "verdict"
        with self.assertRaises(FrozenInstanceError):
            setattr(completion_data, field_name, "RECHAZADO")

    def test_holds_expected_attributes(self):
        completion_data = AnalysisCompletionDTO(
            analysis_id="analysis-123",
            document_name="doc.docx",
            word_count=1200,
            char_count=7500,
            article_type="Científico",
            verdict="PUBLICABLE",
            total_duration_ms=1850.2,
            status="completed",
        )
        self.assertEqual(completion_data.analysis_id, "analysis-123")
        self.assertEqual(completion_data.document_name, "doc.docx")
        self.assertEqual(completion_data.word_count, 1200)
        self.assertEqual(completion_data.char_count, 7500)
        self.assertEqual(completion_data.article_type, "Científico")
        self.assertEqual(completion_data.verdict, "PUBLICABLE")
        self.assertEqual(completion_data.total_duration_ms, 1850.2)
        self.assertEqual(completion_data.status, "completed")
