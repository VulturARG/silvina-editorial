from unittest import TestCase

from src.domain.enums.article_type import ArticleType
from src.domain.enums.section_name import SectionName
from src.domain.structure.required_sections_provider import RequiredSectionsProvider


class TestRequiredSectionsProvider(TestCase):
    def test_scientific_returns_7_sections(self):
        result = RequiredSectionsProvider.get(ArticleType.SCIENTIFIC)
        expected = [
            SectionName.SUMMARY,
            SectionName.INTRODUCTION,
            SectionName.METHODOLOGY,
            SectionName.RESULTS,
            SectionName.DISCUSSION,
            SectionName.CONCLUSIONS,
            SectionName.REFERENCES,
        ]
        self.assertEqual(result, expected)

    def test_popular_science_returns_5_sections(self):
        result = RequiredSectionsProvider.get(ArticleType.POPULAR_SCIENCE)
        expected = [
            SectionName.SUMMARY,
            SectionName.INTRODUCTION,
            SectionName.DEVELOPMENT,
            SectionName.CONCLUSIONS,
            SectionName.REFERENCES,
        ]
        self.assertEqual(result, expected)

    def test_opinion_returns_3_sections(self):
        result = RequiredSectionsProvider.get(ArticleType.OPINION)
        expected = [
            SectionName.INTRODUCTION,
            SectionName.ARGUMENTATION,
            SectionName.CONCLUSIONS,
        ]
        self.assertEqual(result, expected)

    def test_unknown_returns_empty_list(self):
        result = RequiredSectionsProvider.get(ArticleType.UNKNOWN)
        self.assertEqual(result, [])

    def test_desarrollo_not_in_scientific(self):
        result = RequiredSectionsProvider.get(ArticleType.SCIENTIFIC)
        self.assertNotIn(SectionName.DEVELOPMENT, result)

    def test_desarrollo_not_in_opinion(self):
        result = RequiredSectionsProvider.get(ArticleType.OPINION)
        self.assertNotIn(SectionName.DEVELOPMENT, result)
