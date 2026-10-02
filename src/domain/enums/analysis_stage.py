from enum import Enum


class AnalysisStage(Enum):
    """Execution stages of the manuscript analysis pipeline."""

    EXTRACT_CONTENT = "extract_content"
    EXTRACT_CITATIONS = "extract_citations"
    VALIDATE_APA = "validate_apa"
    CHECK_GRAMMAR = "check_grammar"
    CLASSIFY_ARTICLE = "classify_article"
    ANALYZE_QUALITY = "analyze_quality"
    VALIDATE_STRUCTURE = "validate_structure"
    MATCH_CITATIONS = "match_citations"
    INSPECT_FORMAT = "inspect_format"
    BUILD_RECOMMENDATIONS = "build_recommendations"
