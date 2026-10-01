from unittest import TestCase

from src.domain.enums.analysis_stage import AnalysisStage


class TestAnalysisStage(TestCase):
    def test_members_and_values(self):
        self.assertEqual(AnalysisStage.EXTRACT_CONTENT.value, "extract_content")
        self.assertEqual(AnalysisStage.EXTRACT_CITATIONS.value, "extract_citations")
        self.assertEqual(AnalysisStage.VALIDATE_APA.value, "validate_apa")
        self.assertEqual(AnalysisStage.CHECK_GRAMMAR.value, "check_grammar")
        self.assertEqual(AnalysisStage.CLASSIFY_ARTICLE.value, "classify_article")
        self.assertEqual(AnalysisStage.ANALYZE_QUALITY.value, "analyze_quality")
        self.assertEqual(AnalysisStage.VALIDATE_STRUCTURE.value, "validate_structure")
        self.assertEqual(AnalysisStage.MATCH_CITATIONS.value, "match_citations")
        self.assertEqual(AnalysisStage.INSPECT_FORMAT.value, "inspect_format")
        self.assertEqual(AnalysisStage.BUILD_RECOMMENDATIONS.value, "build_recommendations")

    def test_lookup_by_value(self):
        self.assertIs(AnalysisStage("extract_content"), AnalysisStage.EXTRACT_CONTENT)
        self.assertIs(AnalysisStage("extract_citations"), AnalysisStage.EXTRACT_CITATIONS)
        self.assertIs(AnalysisStage("validate_apa"), AnalysisStage.VALIDATE_APA)
        self.assertIs(AnalysisStage("check_grammar"), AnalysisStage.CHECK_GRAMMAR)
        self.assertIs(AnalysisStage("classify_article"), AnalysisStage.CLASSIFY_ARTICLE)
        self.assertIs(AnalysisStage("analyze_quality"), AnalysisStage.ANALYZE_QUALITY)
        self.assertIs(AnalysisStage("validate_structure"), AnalysisStage.VALIDATE_STRUCTURE)
        self.assertIs(AnalysisStage("match_citations"), AnalysisStage.MATCH_CITATIONS)
        self.assertIs(AnalysisStage("inspect_format"), AnalysisStage.INSPECT_FORMAT)
        self.assertIs(AnalysisStage("build_recommendations"), AnalysisStage.BUILD_RECOMMENDATIONS)

    def test_invalid_value_raises_value_error(self):
        with self.assertRaises(ValueError):
            AnalysisStage("invalid")

    def test_member_count(self):
        self.assertEqual(len(AnalysisStage), 10)

    def test_importable_independently(self):
        self.assertIsNotNone(AnalysisStage)
