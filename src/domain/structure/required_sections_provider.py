from src.domain.enums.article_type import ArticleType
from src.domain.enums.section_name import SectionName


class RequiredSectionsProvider:
    """Returns the canonical required sections for each article type."""

    @staticmethod
    def get(article_type: ArticleType) -> list[SectionName]:
        if article_type == ArticleType.SCIENTIFIC:
            return [
                SectionName.SUMMARY,
                SectionName.INTRODUCTION,
                SectionName.METHODOLOGY,
                SectionName.RESULTS,
                SectionName.DISCUSSION,
                SectionName.CONCLUSIONS,
                SectionName.REFERENCES,
            ]
        if article_type == ArticleType.POPULAR_SCIENCE:
            return [
                SectionName.SUMMARY,
                SectionName.INTRODUCTION,
                SectionName.DEVELOPMENT,
                SectionName.CONCLUSIONS,
                SectionName.REFERENCES,
            ]
        if article_type == ArticleType.OPINION:
            return [
                SectionName.INTRODUCTION,
                SectionName.ARGUMENTATION,
                SectionName.CONCLUSIONS,
            ]
        return []
