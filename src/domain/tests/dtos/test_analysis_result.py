from dataclasses import FrozenInstanceError
from unittest import TestCase

from src.domain.dtos.analysis_result_dto import AnalysisResultDTO
from src.domain.dtos.base_dto import BaseDTO
from src.domain.dtos.citation_analysis_result_dto import CitationAnalysisResultDTO
from src.domain.dtos.classification_result_dto import ClassificationResultDTO
from src.domain.dtos.document_content_dto import DocumentContentDTO
from src.domain.dtos.quality_result_dto import QualityResultDTO
from src.domain.dtos.structure_validation_result_dto import StructureValidationResultDTO
from src.domain.enums.article_size import ArticleSize
from src.domain.enums.article_type import ArticleType
from src.domain.enums.quality_level import QualityLevel


class TestAnalysisResultDTO(TestCase):
    def _make_analysis_result(self) -> AnalysisResultDTO:
        document_content = DocumentContentDTO(word_count=500, char_count=3000)
        classification = ClassificationResultDTO(
            article_type=ArticleType.SCIENTIFIC,
            article_size=ArticleSize.LONG,
            confidence=0.9,
            reasoning="Scientific article",
        )
        quality = QualityResultDTO(
            overall_score=8.0,
            quality_level=QualityLevel.GOOD,
        )
        structure = StructureValidationResultDTO(is_valid=True)
        citations = CitationAnalysisResultDTO(
            total_citations=10,
            total_references=8,
            matched_count=8,
            unmatched_count=2,
        )
        return AnalysisResultDTO(
            filename="test_article.docx",
            document_content=document_content,
            classification=classification,
            quality=quality,
            structure=structure,
            citations=citations,
        )

    def test_analysis_result_is_subclass_of_base_dto(self):
        self.assertTrue(issubclass(AnalysisResultDTO, BaseDTO))

    def test_analysis_result_is_immutable(self):
        result = self._make_analysis_result()
        with self.assertRaises(FrozenInstanceError):
            result.filename = "other.docx"

    def test_to_dict_returns_all_required_top_level_keys(self):
        result = self._make_analysis_result()
        output = result.to_dict()
        for key in ("filename", "timestamp", "classification", "quality", "structure", "citations"):
            self.assertIn(key, output)

    def test_to_dict_classification_matches_legacy_shape(self):
        result = self._make_analysis_result()
        classification_dict = result.to_dict()["classification"]
        self.assertEqual(
            set(classification_dict.keys()),
            {"category", "confidence", "reasoning"},
        )
        self.assertEqual(classification_dict["category"], ArticleType.SCIENTIFIC.value)

    def test_to_dict_timestamp_is_iso8601_string(self):
        result = self._make_analysis_result()
        timestamp_value = result.to_dict()["timestamp"]
        self.assertIsInstance(timestamp_value, str)
        self.assertEqual(timestamp_value, result.timestamp.isoformat())
