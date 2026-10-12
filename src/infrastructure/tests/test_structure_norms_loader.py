from unittest import TestCase

from src.domain.dtos.structure_norms_dto import StructureNormsDTO
from src.domain.enums.article_type import ArticleType
from src.domain.enums.section_name import SectionName
from src.domain.exceptions.editorial_norms_errors import EditorialNormInvalid
from src.infrastructure.editorial_norms_value_resolver import (
    EditorialNormsValueResolver,
)
from src.infrastructure.structure_norms_loader import StructureNormsLoader


def _make_valid_raw_norms() -> dict[str, dict[str, list[str]]]:
    return {
        "required_sections": {
            "científico": [
                "Resumen",
                "Introducción",
                "Metodología",
                "Resultados",
                "Discusión",
                "Conclusiones",
                "Referencias",
            ],
            "divulgación": [
                "Resumen",
                "Introducción",
                "Desarrollo",
                "Conclusiones",
                "Referencias",
            ],
            "opinión": ["Introducción", "Argumentación", "Conclusiones"],
        },
        "section_aliases": {
            "Resumen": ["resumen", "abstract"],
            "Introducción": ["introducción", "introduccion", "introduction"],
            "Metodología": ["metodología", "metodologia", "methodology"],
            "Resultados": ["resultados", "results"],
            "Discusión": ["discusión", "discusion", "discussion"],
            "Argumentación": ["argumentación", "argumentacion", "argumentation"],
            "Desarrollo": ["desarrollo", "development"],
            "Conclusiones": ["conclusiones", "conclusión", "conclusion"],
            "Referencias": [
                "referencias",
                "bibliografía",
                "bibliografia",
                "fuentes bibliográficas",
            ],
        },
    }


class TestStructureNormsLoader(TestCase):
    def test_loads_structure_norms_dto_when_valid(self):
        loader = StructureNormsLoader(EditorialNormsValueResolver(_make_valid_raw_norms()))

        result = loader.load()

        self.assertIsInstance(result, StructureNormsDTO)
        self.assertEqual(
            result.required_sections[ArticleType.SCIENTIFIC],
            (
                SectionName.SUMMARY,
                SectionName.INTRODUCTION,
                SectionName.METHODOLOGY,
                SectionName.RESULTS,
                SectionName.DISCUSSION,
                SectionName.CONCLUSIONS,
                SectionName.REFERENCES,
            ),
        )
        self.assertNotIn(ArticleType.UNKNOWN, result.required_sections)

    def test_raises_editorial_norm_invalid_when_article_type_label_unknown(self):
        data = _make_valid_raw_norms()
        data["required_sections"]["desconocido"] = ["Resumen"]
        loader = StructureNormsLoader(EditorialNormsValueResolver(data))

        with self.assertRaises(EditorialNormInvalid) as context:
            loader.load()

        self.assertRegex(context.exception.dict()["error"], r"'desconocido'.*\[required_sections\]")

    def test_raises_editorial_norm_invalid_when_unknown_key_present(self):
        data = _make_valid_raw_norms()
        data["required_sections"]["unknown"] = ["Resumen"]
        loader = StructureNormsLoader(EditorialNormsValueResolver(data))

        with self.assertRaises(EditorialNormInvalid) as context:
            loader.load()

        self.assertRegex(context.exception.dict()["error"], r"'unknown'.*\[required_sections\]")

    def test_raises_editorial_norm_invalid_when_article_type_missing(self):
        data = _make_valid_raw_norms()
        del data["required_sections"]["opinión"]
        loader = StructureNormsLoader(EditorialNormsValueResolver(data))

        with self.assertRaises(EditorialNormInvalid) as context:
            loader.load()

        self.assertRegex(context.exception.dict()["error"], r"'opinión'.*\[required_sections\]")

    def test_raises_editorial_norm_invalid_when_required_section_label_unknown(self):
        data = _make_valid_raw_norms()
        data["required_sections"]["opinión"] = ["Introducción", "Sección Inexistente"]
        loader = StructureNormsLoader(EditorialNormsValueResolver(data))

        with self.assertRaises(EditorialNormInvalid) as context:
            loader.load()

        self.assertRegex(
            context.exception.dict()["error"],
            r"'Sección Inexistente'.*\[required_sections\]",
        )

    def test_raises_editorial_norm_invalid_when_section_alias_label_unknown(self):
        data = _make_valid_raw_norms()
        data["section_aliases"]["Alias Invalido"] = ["algo"]
        loader = StructureNormsLoader(EditorialNormsValueResolver(data))

        with self.assertRaises(EditorialNormInvalid) as context:
            loader.load()

        self.assertRegex(
            context.exception.dict()["error"],
            r"'Alias Invalido'.*\[section_aliases\]",
        )

    def test_raises_editorial_norm_invalid_when_empty_list_in_required_sections(self):
        data = _make_valid_raw_norms()
        data["required_sections"]["opinión"] = []
        loader = StructureNormsLoader(EditorialNormsValueResolver(data))

        with self.assertRaises(EditorialNormInvalid) as context:
            loader.load()

        self.assertRegex(context.exception.dict()["error"], r"'opinión'.*\[required_sections\]")

    def test_raises_editorial_norm_invalid_when_required_section_lacks_aliases(self):
        data = _make_valid_raw_norms()
        del data["section_aliases"]["Resumen"]
        loader = StructureNormsLoader(EditorialNormsValueResolver(data))

        with self.assertRaises(EditorialNormInvalid) as context:
            loader.load()

        self.assertRegex(
            context.exception.dict()["error"],
            r"'Resumen'.*(\[required_sections\]|\[section_aliases\])",
        )

    def test_aliases_lowercased_and_deduplicated_preserving_order(self):
        data = _make_valid_raw_norms()
        data["section_aliases"]["Resumen"] = ["  RESUMEN  ", "abstract", "resumen", "Abstract"]
        loader = StructureNormsLoader(EditorialNormsValueResolver(data))

        result = loader.load()

        self.assertEqual(result.section_aliases[SectionName.SUMMARY], ("resumen", "abstract"))

    def test_preserves_order_of_section_aliases(self):
        data = _make_valid_raw_norms()
        loader = StructureNormsLoader(EditorialNormsValueResolver(data))

        result = loader.load()

        expected_order = [
            SectionName.SUMMARY,
            SectionName.INTRODUCTION,
            SectionName.METHODOLOGY,
            SectionName.RESULTS,
            SectionName.DISCUSSION,
            SectionName.ARGUMENTATION,
            SectionName.DEVELOPMENT,
            SectionName.CONCLUSIONS,
            SectionName.REFERENCES,
        ]
        self.assertEqual(list(result.section_aliases.keys()), expected_order)
