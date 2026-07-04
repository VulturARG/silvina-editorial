"""
Unit tests for the DTO-to-legacy dictionary mapping helper in main.py.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.domain.dtos.apa_validation_result_dto import ApaValidationResultDTO
from src.domain.dtos.apa_violation_dto import ApaViolationDTO
from src.domain.dtos.citation_analysis_result_dto import CitationAnalysisResultDTO
from src.domain.dtos.classification_result_dto import ClassificationResultDTO
from src.domain.dtos.document_content_dto import DocumentContentDTO
from src.domain.dtos.grammar_check_result_dto import GrammarCheckResultDTO
from src.domain.dtos.grammar_error_dto import GrammarErrorDTO
from src.domain.dtos.publication_verdict_dto import PublicationVerdictDTO
from src.domain.dtos.quality_result_dto import QualityResultDTO
from src.domain.dtos.recommendation_dto import RecommendationDTO
from src.domain.dtos.report_input_dto import ReportInputDTO
from src.domain.dtos.structure_validation_result_dto import StructureValidationResultDTO
from src.domain.enums.apa_error_type import ApaErrorType
from src.domain.enums.article_size import ArticleSize
from src.domain.enums.article_type import ArticleType
from src.domain.enums.publication_verdict import PublicationVerdict
from src.domain.enums.quality_level import QualityLevel
from src.domain.enums.recommendation_priority import RecommendationPriority


def _build_report_input(
    total_citations: int,
    matched_count: int,
    apa_violations: list,
) -> ReportInputDTO:
    document_content = DocumentContentDTO(
        word_count=1200,
        char_count=8000,
        title="Un Titulo de Prueba",
        authors="Autor Uno",
    )
    classification = ClassificationResultDTO.create(
        article_type=ArticleType.SCIENTIFIC,
        article_size=ArticleSize.SHORT,
        confidence=0.85,
        reasoning="Contiene metodología IMRyD",
    )
    quality = QualityResultDTO(
        overall_score=8.2,
        quality_level=QualityLevel.GOOD,
        dimension_scores={"claridad": {"score": 8.0, "feedback": "Bien"}},
    )
    grammar = GrammarCheckResultDTO(
        score=9.0,
        feedback="Sin errores relevantes",
        errors=[
            GrammarErrorDTO(
                number=1,
                message="Error de tipeo",
                context="algun contexto",
                offset=10,
                length=3,
                replacements=["algún"],
            )
        ],
    )
    structure = StructureValidationResultDTO(
        is_valid=True,
        missing_sections=[],
        section_details={},
    )
    citations = CitationAnalysisResultDTO(
        total_citations=total_citations,
        total_references=total_citations,
        matched_count=matched_count,
        unmatched_count=total_citations - matched_count,
        citations_by_type={"author_year": total_citations},
        unmatched_citations=["Smith 2020"] if matched_count < total_citations else [],
    )
    apa_validation = ApaValidationResultDTO(
        is_valid=len(apa_violations) == 0,
        violation_count=len(apa_violations),
        violations=apa_violations,
    )
    recommendations = [
        RecommendationDTO(priority=RecommendationPriority.HIGH, message="Corregir gramática"),
    ]
    verdict = PublicationVerdictDTO(
        verdict=PublicationVerdict.APPROVED,
        message="Apto para publicación",
    )

    return ReportInputDTO(
        filename="/tmp/some/path/documento.docx",
        document_content=document_content,
        classification=classification,
        quality=quality,
        grammar=grammar,
        structure=structure,
        citations=citations,
        apa_validation=apa_validation,
        recommendations=recommendations,
        verdict=verdict,
        eumic_violations=[],
    )


class TestMapReportToLegacyDict(unittest.TestCase):
    def setUp(self):
        from main import SilvinaEditorialAssistant

        self.assistant = SilvinaEditorialAssistant.__new__(SilvinaEditorialAssistant)

    def test_maps_filename_to_basename(self):
        report = _build_report_input(total_citations=5, matched_count=5, apa_violations=[])
        legacy = self.assistant._map_report_to_legacy_dict(report)
        self.assertEqual(legacy["filename"], "documento.docx")

    def test_maps_document_info_fields(self):
        report = _build_report_input(total_citations=5, matched_count=5, apa_violations=[])
        legacy = self.assistant._map_report_to_legacy_dict(report)
        self.assertEqual(legacy["document_info"]["title"], "Un Titulo de Prueba")
        self.assertEqual(legacy["document_info"]["word_count"], 1200)
        self.assertEqual(legacy["document_info"]["estimated_pages"], 1200 // 250)

    def test_maps_citations_analysis_with_no_apa_violations(self):
        report = _build_report_input(total_citations=5, matched_count=4, apa_violations=[])
        legacy = self.assistant._map_report_to_legacy_dict(report)
        citations_analysis = legacy["citations_analysis"]
        self.assertEqual(citations_analysis["total_citations"], 5)
        self.assertEqual(citations_analysis["matched_count"], 4)
        self.assertEqual(citations_analysis["unmatched_count"], 1)
        self.assertEqual(citations_analysis["apa_violations"], 0)
        self.assertTrue(citations_analysis["apa_compliant"])

    def test_maps_apa_violations_into_dict_entries(self):
        violation = ApaViolationDTO(
            citation_text="Smith 2020",
            error_type=ApaErrorType.YEAR_FORMAT_ERROR,
            location=3,
            explanation="Falta el año entre paréntesis",
            correction="(Smith, 2020)",
        )
        report = _build_report_input(total_citations=5, matched_count=5, apa_violations=[violation])
        legacy = self.assistant._map_report_to_legacy_dict(report)
        violations = legacy["apa_validation"]["violations"]
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0]["citation"], "Smith 2020")
        self.assertEqual(violations[0]["error_type"], ApaErrorType.YEAR_FORMAT_ERROR.value)
        self.assertEqual(violations[0]["correction"], "(Smith, 2020)")
        self.assertFalse(legacy["citations_analysis"]["apa_compliant"])

    def test_maps_recommendations_to_priority_message_dicts(self):
        report = _build_report_input(total_citations=5, matched_count=5, apa_violations=[])
        legacy = self.assistant._map_report_to_legacy_dict(report)
        self.assertEqual(
            legacy["recommendations"],
            [{"priority": "alta", "message": "Corregir gramática"}],
        )


if __name__ == "__main__":
    unittest.main()
