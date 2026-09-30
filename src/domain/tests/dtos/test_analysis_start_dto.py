from dataclasses import FrozenInstanceError
from unittest import TestCase

from src.domain.dtos.analysis_start_dto import AnalysisStartDTO
from src.domain.dtos.base_dto import BaseDTO


class TestAnalysisStartDTO(TestCase):
    def test_is_subclass_of_base_dto(self):
        self.assertTrue(issubclass(AnalysisStartDTO, BaseDTO))

    def test_frozen_raises_on_mutation(self):
        start_data = AnalysisStartDTO(
            analysis_id="analysis-123",
            document_name="doc.docx",
        )
        field_name = "analysis_id"
        with self.assertRaises(FrozenInstanceError):
            setattr(start_data, field_name, "mutation")

    def test_holds_expected_attributes(self):
        start_data = AnalysisStartDTO(
            analysis_id="analysis-123",
            document_name="doc.docx",
        )
        self.assertEqual(start_data.analysis_id, "analysis-123")
        self.assertEqual(start_data.document_name, "doc.docx")
