from unittest.mock import MagicMock

from src.domain.dtos.report_input_dto import ReportInputDTO


class ReportFixtures:
    @staticmethod
    def make_grammar_mock(score: float = 7.5, errors: list | None = None) -> MagicMock:
        grammar = MagicMock()
        grammar.score = score
        grammar.feedback = "Good grammar"
        grammar.errors = errors if errors is not None else []
        return grammar

    @staticmethod
    def make_quality_mock(overall_score: float = 8.0) -> MagicMock:
        quality = MagicMock()
        quality.overall_score = overall_score
        quality.dimension_scores = {}
        return quality

    @staticmethod
    def make_citations_mock(total: int = 5, matched: int = 5, references: int = 5) -> MagicMock:
        citations = MagicMock()
        citations.total_citations = total
        citations.total_references = references
        citations.matched_count = matched
        return citations

    @staticmethod
    def make_apa_validation_mock(violations: list | None = None) -> MagicMock:
        apa = MagicMock()
        apa.violations = violations if violations is not None else []
        return apa

    @staticmethod
    def make_doc_content_mock(
        word_count: int = 2500, char_count: int = 12000, title: str = "Test"
    ) -> MagicMock:
        doc_content = MagicMock()
        doc_content.word_count = word_count
        doc_content.char_count = char_count
        doc_content.title = title
        doc_content.authors = "Test Author"
        return doc_content

    @staticmethod
    def make_classification_mock(article_type_value: str = "Investigación") -> MagicMock:
        classification = MagicMock()
        classification.article_type.value = article_type_value
        classification.confidence = 0.9
        classification.reasoning = "Test reasoning"
        return classification

    @staticmethod
    def make_structure_mock(is_valid: bool = True) -> MagicMock:
        structure = MagicMock()
        structure.is_valid = is_valid
        structure.missing_sections = []
        return structure

    @staticmethod
    def make_report_input_dto(**overrides) -> ReportInputDTO:
        defaults = {
            "filename": "test.docx",
            "document_content": ReportFixtures.make_doc_content_mock(),
            "classification": ReportFixtures.make_classification_mock(),
            "quality": ReportFixtures.make_quality_mock(),
            "grammar": ReportFixtures.make_grammar_mock(),
            "structure": ReportFixtures.make_structure_mock(),
            "citations": ReportFixtures.make_citations_mock(),
            "apa_validation": ReportFixtures.make_apa_validation_mock(),
            "recommendations": [],
        }
        defaults.update(overrides)
        return ReportInputDTO(**defaults)
