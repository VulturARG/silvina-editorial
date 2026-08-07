from enum import Enum
from json import dump
from pathlib import Path
from typing import Any

from src.domain.dtos.base_dto import BaseDTO
from src.domain.dtos.report_input_dto import ReportInputDTO
from src.domain.report.report_export_port import ReportExportPort


class JsonReportAdapter(ReportExportPort):
    """Export analysis reports to JSON, matching the legacy on-disk report shape."""

    def export(self, report_input: ReportInputDTO, output_path: str) -> bool:
        legacy_shape = self._to_legacy_shape(report_input)
        json_data = self._prepare_for_json(legacy_shape)

        with open(output_path, "w", encoding="utf-8") as file:
            dump(json_data, file, ensure_ascii=False, indent=2)

        return True

    @staticmethod
    def _to_legacy_shape(report_input: ReportInputDTO) -> dict[str, Any]:
        """Reproduce main.py's `_map_report_to_legacy_dict` field mapping."""
        document_content = report_input.document_content
        classification = report_input.classification
        quality = report_input.quality
        grammar = report_input.grammar
        structure = report_input.structure
        citations_analysis = report_input.citations
        apa_validation = report_input.apa_validation

        return {
            "filename": Path(report_input.filename).name,
            "document_info": {
                "title": document_content.title,
                "authors": document_content.authors,
                "word_count": document_content.word_count,
                "char_count": document_content.char_count,
                "estimated_pages": document_content.word_count // 250,
            },
            "classification": {
                "category": classification.article_type,
                "article_size": classification.article_size,
                "confidence": classification.confidence,
                "reasoning": classification.reasoning,
            },
            "quality_analysis": {
                "overall_score": quality.overall_score,
                "quality_level": quality.quality_level,
                "gramatica": {
                    "score": grammar.score,
                    "feedback": grammar.feedback,
                    "errors": grammar.errors,
                },
                "dimensions": quality.dimension_scores,
            },
            "structure_validation": {
                "is_valid": structure.is_valid,
                "missing_sections": structure.missing_sections,
                "details": structure.section_details,
            },
            "citations_analysis": {
                "total_citations": citations_analysis.total_citations,
                "total_references": citations_analysis.total_references,
                "matched_count": citations_analysis.matched_count,
                "unmatched_count": citations_analysis.unmatched_count,
                "by_type": citations_analysis.citations_by_type,
                "unmatched_citations": citations_analysis.unmatched_citations[:20],
                "apa_violations": apa_validation.violation_count,
                "apa_compliant": apa_validation.is_valid,
            },
            "apa_validation": {
                "violations": [
                    {
                        "citation": violation.citation_text,
                        "error_type": violation.error_type.value,
                        "location": violation.location,
                        "explanation": violation.explanation,
                        "correction": violation.correction,
                    }
                    for violation in apa_validation.violations
                ],
                "report": "",
            },
            "recommendations": [
                {"priority": recommendation.priority.value, "message": recommendation.message}
                for recommendation in report_input.recommendations
            ],
        }

    @staticmethod
    def _prepare_for_json(data: Any) -> Any:
        """Recursively convert enums and DTOs into JSON-serializable structures."""
        if isinstance(data, dict):
            return {key: JsonReportAdapter._prepare_for_json(value) for key, value in data.items()}
        if isinstance(data, list):
            return [JsonReportAdapter._prepare_for_json(item) for item in data]
        if isinstance(data, Enum):
            return data.value
        if isinstance(data, BaseDTO):
            return JsonReportAdapter._prepare_for_json(data.as_dict())
        return data
