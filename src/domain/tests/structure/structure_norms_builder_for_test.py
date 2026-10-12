from src.domain.dtos.structure_norms_dto import StructureNormsDTO
from src.domain.enums.article_type import ArticleType
from src.domain.enums.section_name import SectionName


def build_structure_norms_for_test() -> StructureNormsDTO:
    """Build a StructureNormsDTO populated with canonical editorial standards."""
    return StructureNormsDTO(
        required_sections={
            ArticleType.SCIENTIFIC: (
                SectionName.SUMMARY,
                SectionName.INTRODUCTION,
                SectionName.METHODOLOGY,
                SectionName.RESULTS,
                SectionName.DISCUSSION,
                SectionName.CONCLUSIONS,
                SectionName.REFERENCES,
            ),
            ArticleType.POPULAR_SCIENCE: (
                SectionName.SUMMARY,
                SectionName.INTRODUCTION,
                SectionName.DEVELOPMENT,
                SectionName.CONCLUSIONS,
                SectionName.REFERENCES,
            ),
            ArticleType.OPINION: (
                SectionName.INTRODUCTION,
                SectionName.ARGUMENTATION,
                SectionName.CONCLUSIONS,
            ),
        },
        section_aliases={
            SectionName.SUMMARY: ("resumen", "abstract"),
            SectionName.INTRODUCTION: ("introducción", "introduccion", "introduction"),
            SectionName.METHODOLOGY: ("metodología", "metodologia", "methodology"),
            SectionName.RESULTS: ("resultados", "results"),
            SectionName.DISCUSSION: ("discusión", "discusion", "discussion"),
            SectionName.ARGUMENTATION: ("argumentación", "argumentacion", "argumentation"),
            SectionName.DEVELOPMENT: ("desarrollo", "development"),
            SectionName.CONCLUSIONS: ("conclusiones", "conclusión", "conclusion"),
            SectionName.REFERENCES: (
                "referencias",
                "bibliografía",
                "bibliografia",
                "fuentes bibliográficas",
            ),
        },
    )
