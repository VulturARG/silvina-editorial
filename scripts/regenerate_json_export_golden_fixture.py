"""Regenerate the golden JSON export fixture used by JsonReportAdapter's parity test.

This script is a self-contained, FROZEN copy of the pre-change `main.py` logic
(`_map_report_to_legacy_dict` + `_prepare_for_json` + `json.dump`), as it existed
before the `json-report-export-adapter` change. It is deliberately NOT imported
from `main.py`, because that logic is deleted from `main.py` in a later phase of
this same change (Phase 5) — importing it would break this script once that
phase lands.

Regenerate the golden fixture ONLY after an intentional, reviewed change to the
legacy JSON export shape (i.e. a deliberate format change to `JsonReportAdapter`
that all consumers of the exported `.json` file have agreed to). Running this
script blindly to "fix" a failing golden-parity test hides real regressions.

Usage:
    .venv\\Scripts\\python scripts\\regenerate_json_export_golden_fixture.py
"""

from enum import Enum
from json import dump
from pathlib import Path
from sys import path
from typing import Any

project_root = Path(__file__).parent.parent
path.insert(0, str(project_root))

from src.domain.dtos.base_dto import BaseDTO  # noqa: E402
from src.domain.dtos.report_input_dto import ReportInputDTO  # noqa: E402
from src.infrastructure.tests.adapters.report.json_fixtures import (  # noqa: E402
    JsonReportFixtures,
)

_GOLDEN_FIXTURE_PATH = (
    project_root
    / "src"
    / "infrastructure"
    / "tests"
    / "adapters"
    / "report"
    / "fixtures"
    / "json_export_golden.json"
)


def map_report_to_legacy_dict(report: ReportInputDTO) -> dict[str, Any]:
    """Frozen copy of pre-change main.py's `_map_report_to_legacy_dict`."""
    document_content = report.document_content
    classification = report.classification
    quality = report.quality
    grammar = report.grammar
    structure = report.structure
    citations_analysis = report.citations
    apa_validation = report.apa_validation

    return {
        "filename": Path(report.filename).name,
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
                    "citation": v.citation_text,
                    "error_type": v.error_type.value,
                    "location": v.location,
                    "explanation": v.explanation,
                    "correction": v.correction,
                }
                for v in apa_validation.violations
            ],
            "report": "",
        },
        "recommendations": [
            {"priority": r.priority.value, "message": r.message} for r in report.recommendations
        ],
    }


def prepare_for_json(data: Any) -> Any:
    """Frozen copy of pre-change main.py's `_prepare_for_json`."""
    if isinstance(data, dict):
        return {key: prepare_for_json(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [prepare_for_json(item) for item in data]
    elif isinstance(data, Enum):
        return data.value
    elif isinstance(data, BaseDTO):
        return prepare_for_json(data.as_dict())
    else:
        return data


def main() -> None:
    """Generate the golden JSON fixture from JsonReportFixtures using the frozen legacy pipeline."""
    report_input = JsonReportFixtures.make_real_report_input_dto()
    legacy_dict = map_report_to_legacy_dict(report_input)
    json_data = prepare_for_json(legacy_dict)

    _GOLDEN_FIXTURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_GOLDEN_FIXTURE_PATH, "w", encoding="utf-8") as file:
        dump(json_data, file, ensure_ascii=False, indent=2)

    print(f"Golden fixture written to {_GOLDEN_FIXTURE_PATH}")


if __name__ == "__main__":
    main()
