from unittest import TestCase

from src.domain.enums.article_type import ArticleType
from src.domain.enums.recommendation_priority import RecommendationPriority
from src.infrastructure.adapters.report.json_report_adapter import JsonReportAdapter
from src.infrastructure.tests.adapters.report.json_fixtures import JsonReportFixtures


class TestJsonReportAdapterPrepareForJson(TestCase):
    def test_converts_enum_to_its_value(self):
        result = JsonReportAdapter._prepare_for_json(ArticleType.SCIENTIFIC)

        self.assertEqual(result, "científico")

    def test_converts_different_enum_to_its_own_value(self):
        result = JsonReportAdapter._prepare_for_json(RecommendationPriority.HIGH)

        self.assertEqual(result, "alta")

    def test_converts_nested_base_dto_to_dict(self):
        report_input = JsonReportFixtures.make_real_report_input_dto()

        result = JsonReportAdapter._prepare_for_json(report_input.grammar)

        self.assertEqual(result["score"], 9.0)
        self.assertEqual(result["feedback"], "Muy buena redaccion.")

    def test_recurses_into_list_items(self):
        result = JsonReportAdapter._prepare_for_json(
            [ArticleType.SCIENTIFIC, RecommendationPriority.LOW]
        )

        self.assertEqual(result, ["científico", "baja"])

    def test_recurses_into_dict_values(self):
        result = JsonReportAdapter._prepare_for_json(
            {"category": ArticleType.OPINION, "priority": RecommendationPriority.MEDIUM}
        )

        self.assertEqual(result, {"category": "opinión", "priority": "media"})

    def test_passes_through_scalar_values_unchanged(self):
        self.assertEqual(JsonReportAdapter._prepare_for_json("plain text"), "plain text")
        self.assertEqual(JsonReportAdapter._prepare_for_json(42), 42)
        self.assertIsNone(JsonReportAdapter._prepare_for_json(None))
